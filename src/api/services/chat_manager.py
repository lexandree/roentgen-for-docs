import uuid
import os
import random
import base64
import httpx
import json
import re
from datetime import datetime, timezone
from src.api.db.database import get_db
from src.api.config import settings

# A single, reusable httpx client for performance
# It's important to manage the client's lifecycle in a real FastAPI app (e.g., with lifespan events)
# but for this service, a module-level client is sufficient.
http_client = httpx.AsyncClient(timeout=600.0)

class ChatManager:

    # Load GBNF grammar once at module/class level to avoid reading file on every request
    try:
        with open("src/api/grammar/report.gbnf", "r") as f:
            GBNF_GRAMMAR = f.read()
    except Exception:
        GBNF_GRAMMAR = None

    async def dispatch_inference_to_worker(self, messages: list, system_prompt_text: str | None = None, route: str = "local_python", system_prompt_type: int = 1) -> str:
        """
        Selects a worker and sends the full OpenAI-style messages array.
        Supports both custom python worker (/infer) and OpenAI-compatible endpoints (/v1/chat/completions).
        """
        if not settings.inference_workers:
            raise ValueError("No inference workers configured.")

        # Get the URL for the specified route, or fallback to the first one available
        worker_config = settings.inference_workers.get(route)
        if not worker_config:
             worker_url = next(iter(settings.inference_workers.values())).get("url")
        else:
             worker_url = worker_config.get("url")

        if not worker_url:
            raise ValueError(f"No valid URL found for route {route}.")

        if not system_prompt_text:
            system_prompt_text = "You are an expert radiologist AI assistant. Be highly concise, factual, and direct. Do NOT use disclaimers like 'I am an AI' or 'Consult a doctor'. If you need to reason before answering, ALWAYS wrap your reasoning entirely inside <think>...</think> tags."

        # Determine worker type based on URL
        if worker_url.endswith("/v1/chat/completions"):
            # OpenAI compatible (like llama-server)
            inference_endpoint = worker_url
            
            import copy
            final_messages = copy.deepcopy(messages)
            
            # Since we now use a custom `medgemma.jinja` template, we no longer need to hack 
            # the system prompt into the first user message. The template handles the "system" role.
            final_messages.insert(0, {"role": "system", "content": system_prompt_text})

            # Calculate dedicated slot ID based on user type to maximize KV cache hits without flushing.
            # Example: type 1 -> slot 0, type 2 -> slot 1, etc.
            # We assume a `-np 3` server setup.
            id_slot = (system_prompt_type - 1) % 3

            payload = {
                "messages": final_messages,
                "temperature": 0.0, # Deterministic medical answers
                "max_tokens": settings.llama_max_tokens,
                "id_slot": id_slot,
                "cache_prompt": True
            }
            if self.GBNF_GRAMMAR:
                payload["grammar"] = self.GBNF_GRAMMAR
        else:
            # Our custom Python worker (/infer) handles the system prompt array injection natively
            system_prompt = {
                "role": "system",
                "content": system_prompt_text
            }
            final_messages = [system_prompt] + messages
            
            inference_endpoint = worker_url if worker_url.endswith("/infer") else f"{worker_url.rstrip('/')}/infer"
            payload = {
                "messages": final_messages
            }

        try:
            response = await http_client.post(inference_endpoint, json=payload, timeout=settings.request_timeout)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            
            response_data = response.json()
            
            # Extract response based on API format
            telemetry = {}
            if "choices" in response_data:
                # OpenAI format
                raw_text = response_data["choices"][0]["message"]["content"].strip()
                usage = response_data.get("usage", {})
                if usage:
                    telemetry = {
                        "input_tokens": usage.get("prompt_tokens"),
                        "output_tokens": usage.get("completion_tokens")
                    }
            else:
                # Custom worker format
                raw_text = response_data.get("report", "Worker did not return a valid report.")
                telemetry = response_data.get("telemetry", {})

            # Clean up potential LLM hallucination formats (JSON/thought blocks)
            cleaned_text = raw_text
            thought_text = ""

            # Try parsing as JSON first (even without markdown blocks)
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    if "response" in data:
                        cleaned_text = data["response"]
                        if "thought" in data:
                            thought_text = data["thought"]
                except json.JSONDecodeError:
                    pass

            # If no thought found yet, try extracting from tags
            if not thought_text:
                think_match = re.search(r'<think>(.*?)</think>', cleaned_text, flags=re.DOTALL)
                if think_match:
                    thought_text = think_match.group(1).strip()
                    cleaned_text = re.sub(r'<think>.*?</think>', '', cleaned_text, flags=re.DOTALL).strip()
                else:
                    thought_match = re.search(r'thought\n(.*?)(\n\n|\Z)', cleaned_text, flags=re.DOTALL)
                    if thought_match:
                        thought_text = thought_match.group(1).strip()
                        cleaned_text = re.sub(r'thought\n.*?(?=\n\n|\Z)', '', cleaned_text, flags=re.DOTALL).strip()
                        
            # If the model ONLY output thoughts and nothing else (e.g. got cut off by max_tokens),
            # we should return the thoughts as the main response so the user doesn't get an empty message.
            if not cleaned_text and thought_text:
                cleaned_text = thought_text

            # Safer fallback: if the model completely ignores tags but outputs a lot of text, 
            # we do NOT try to guess based on languages or paragraphs as it causes false positives.
            # We rely on the system prompt to enforce formatting. 
            # If it still fails, the user gets the raw output, which is safer than truncating a real medical answer.

            return {
                "report": cleaned_text.strip(),
                "thought": thought_text.strip(),
                "raw_text": raw_text,
                "telemetry": telemetry
            }

        except httpx.HTTPStatusError as e:
            # The worker returned an error response (e.g., 500)
            print(f"Error from worker {worker_url}: {e.response.text}")
            raise Exception(f"Inference worker failed with status {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            # Network-level error (e.g., can't connect)
            print(f"Could not connect to worker {worker_url}: {e}")
            raise Exception(f"Failed to connect to inference worker: {e}")

    async def get_or_create_session(self, telegram_id: int, db, default_route: str = None) -> tuple[str, str]:
        cursor = await db.execute("SELECT session_id, last_activity, current_route FROM session_contexts WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        
        now = datetime.now(timezone.utc)
        if row:
            # Check parameterized expiry
            last_activity = row["last_activity"]
            if isinstance(last_activity, str):
                last_activity = datetime.fromisoformat(last_activity)
            
            if (now - last_activity).total_seconds() > settings.session_timeout_seconds:
                await self.clear_session(telegram_id, db)
            else:
                route_to_use = default_route or row["current_route"]
                if default_route and default_route != row["current_route"]:
                    await db.execute("UPDATE session_contexts SET last_activity = ?, current_route = ? WHERE session_id = ?", (now, default_route, row["session_id"]))
                else:
                    await db.execute("UPDATE session_contexts SET last_activity = ? WHERE session_id = ?", (now, row["session_id"]))
                await db.commit()
                return row["session_id"], route_to_use
                
        # Create new session
        session_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO session_contexts (session_id, telegram_id, last_activity, has_active_image, current_route) VALUES (?, ?, ?, 0, ?)",
            (session_id, telegram_id, now, default_route)
        )
        await db.commit()
        return session_id, default_route

    async def add_message(self, session_id: str, role: str, content: str, db):
        await db.execute(
            "INSERT INTO message_history (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content)
        )
        await db.commit()

    async def get_history(self, session_id: str, db) -> list:
        cursor = await db.execute("SELECT role, content FROM message_history WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
        rows = await cursor.fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in rows]

    async def set_active_image(self, session_id: str, has_active: bool, db):
        await db.execute("UPDATE session_contexts SET has_active_image = ? WHERE session_id = ?", (int(has_active), session_id))
        await db.commit()

    async def clear_session(self, telegram_id: int, db):
        cursor = await db.execute("SELECT session_id FROM session_contexts WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        if row:
            session_id = row["session_id"]
            # Cascade delete in SQLite takes care of history
            await db.execute("DELETE FROM session_contexts WHERE session_id = ?", (session_id,))
            await db.commit()
            
        # Attempt to clear KV cache on all configured inference workers to free VRAM
        for route_id, config in settings.inference_workers.items():
            worker_url = config.get("url", "")
            if not worker_url:
                continue
                
            # If the URL is our custom Python worker (ends with /infer)
            if worker_url.endswith("/infer"):
                clear_endpoint = worker_url.replace("/infer", "/clear")
                try:
                    # Fire and forget / clear timeout is low
                    # In a production setting, this should ideally be an async background task 
                    # so we don't slow down the response if workers are unresponsive.
                    import asyncio
                    asyncio.create_task(
                        http_client.post(clear_endpoint, timeout=3.0)
                    )
                except Exception as e:
                    print(f"Failed to clear VRAM for worker {route_id} at {clear_endpoint}: {e}")

    async def create_interaction_log(self, telegram_id: int, route: str, task_type: str, images_count: int, db) -> int:
        cursor = await db.execute(
            "INSERT INTO interaction_logs (telegram_id, route, task_type, images_count, status) VALUES (?, ?, ?, ?, 'queued')",
            (telegram_id, route, task_type, images_count)
        )
        await db.commit()
        return cursor.lastrowid

    async def update_interaction_log(self, log_id: int, status: str, db, latency: float = None, input_tokens: int = None, output_tokens: int = None):
        if status in ['completed', 'failed']:
            await db.execute(
                "UPDATE interaction_logs SET status = ?, completed_at = CURRENT_TIMESTAMP, latency = ?, input_tokens = ?, output_tokens = ? WHERE id = ?",
                (status, latency, input_tokens, output_tokens, log_id)
            )
        else:
            await db.execute(
                "UPDATE interaction_logs SET status = ? WHERE id = ?",
                (status, log_id)
            )
        await db.commit()

    async def check_workers_health(self) -> dict:
        from urllib.parse import urlparse
        statuses = {}
        for route_id, config in settings.inference_workers.items():
            url = config.get("url")
            name = config.get("name", route_id)
            
            if not url:
                statuses[route_id] = {"name": name, "status": "offline", "reason": "No URL"}
                continue
                
            # Serverless protection: By default, do not ping https URLs unless explicitly marked pingable
            # Local/tunnel URLs (http://) are pinged by default unless explicitly disabled
            is_https = url.startswith("https://")
            pingable_default = not is_https
            is_pingable = config.get("pingable", pingable_default)

            if not is_pingable:
                statuses[route_id] = {
                    "name": name, 
                    "status": "serverless", 
                    "reason": "Wakes up on request only"
                }
                continue
                
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            try:
                # 3-second timeout: enough to check if a TCP connection can be established
                response = await http_client.get(base_url, timeout=3.0)
                # Any HTTP response (even 404/405) means the server is reachable
                statuses[route_id] = {"name": name, "status": "online"}
            except httpx.TimeoutException:
                # RunPod or Colab might be asleep and taking time to wake up
                statuses[route_id] = {"name": name, "status": "timeout (waking up?)"}
            except httpx.RequestError:
                # Connection refused usually means the worker or tunnel is down
                statuses[route_id] = {"name": name, "status": "offline"}
            except Exception as e:
                statuses[route_id] = {"name": name, "status": "error"}
                
        return statuses

chat_manager = ChatManager()
