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
http_client = httpx.AsyncClient(timeout=300.0)

class ChatManager:

    async def dispatch_inference_to_worker(self, messages: list, system_prompt_text: str | None = None, route: str = "local_python") -> str:
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

        if not system_prompt_text:            system_prompt_text = "You are an expert radiologist AI assistant. Be highly concise, factual, and direct. Do NOT use disclaimers like 'I am an AI' or 'Consult a doctor'."

        # Determine worker type based on URL
        if worker_url.endswith("/v1/chat/completions"):
            # OpenAI compatible (like llama-server)
            inference_endpoint = worker_url
            
            import copy
            final_messages = copy.deepcopy(messages)
            
            # For strict chat templates (like Gemma), the system prompt often causes Jinja errors
            # if sent as a separate role because the template expects strict user/assistant alternation.
            # We squash the system prompt into the first user message.
            if final_messages and final_messages[0]["role"] == "user":
                first_msg_content = final_messages[0]["content"]
                if isinstance(first_msg_content, list):
                    # Multimodal content
                    text_found = False
                    for part in first_msg_content:
                        if part["type"] == "text":
                            part["text"] = f"[{system_prompt_text}]\n\n{part['text']}"
                            text_found = True
                            break
                    if not text_found:
                        first_msg_content.append({"type": "text", "text": f"[{system_prompt_text}]"})
                else:
                    # String content
                    final_messages[0]["content"] = f"[{system_prompt_text}]\n\n{first_msg_content}"
            elif final_messages and final_messages[0]["role"] != "system":
                # Fallback if history is weird and first message is not user
                final_messages.insert(0, {"role": "user", "content": f"[{system_prompt_text}]\nPlease continue."})

            # Gemma jinja template STRICTLY requires alternating user -> assistant -> user
            # We must ensure there are no two users or two assistants in a row, and no system roles.
            cleaned_alternating_messages = []
            expected_role = "user"
            
            for msg in final_messages:
                if msg["role"] == "system":
                    continue # Skip any stray system roles
                
                # Treat 'model' as 'assistant' to satisfy the Jinja template's literal string check
                current_role = "assistant" if msg["role"] == "model" else msg["role"]
                
                if current_role == expected_role:
                    cleaned_alternating_messages.append({"role": current_role, "content": msg["content"]})
                    expected_role = "assistant" if current_role == "user" else "user"
                else:
                    # If we get two users in a row, or two assistants in a row, we merge their content
                    # to maintain the strict alternation required by Gemma.
                    if cleaned_alternating_messages:
                        prev_msg = cleaned_alternating_messages[-1]
                        
                        # Merge content
                        if isinstance(prev_msg["content"], str) and isinstance(msg["content"], str):
                            prev_msg["content"] += f"\n\n{msg['content']}"
                        elif isinstance(prev_msg["content"], list) and isinstance(msg["content"], list):
                            prev_msg["content"].extend(msg["content"])
                        elif isinstance(prev_msg["content"], list) and isinstance(msg["content"], str):
                            prev_msg["content"].append({"type": "text", "text": msg["content"]})
                        elif isinstance(prev_msg["content"], str) and isinstance(msg["content"], list):
                            new_content = [{"type": "text", "text": prev_msg["content"]}]
                            new_content.extend(msg["content"])
                            prev_msg["content"] = new_content

            payload = {
                "messages": cleaned_alternating_messages,
                "temperature": 0.0, # Deterministic medical answers
                "max_tokens": settings.llama_max_tokens
            }
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
                        
            # Heuristic fallback for unstructured Chain-of-Thought (e.g. numbered lists followed by a conclusion)
            if not thought_text:
                paragraphs = raw_text.split('\n\n')
                if len(paragraphs) > 1:
                    first_para = paragraphs[0].strip()
                    if first_para.startswith("1. ") or "I understand" in first_para or "The user" in first_para or "I need to" in first_para:
                        valid_paras = [p.strip() for p in paragraphs if p.strip()]
                        if len(valid_paras) > 1:
                            thought_text = "\n\n".join(valid_paras[:-1])
                            last_para = valid_paras[-1]
                            
                            # Check if an English reasoning sentence is glued directly to the Russian final answer
                            cyrillic_transition = re.search(r'^(.*?)([.?!])\s*([А-Яа-яЁё].*)$', last_para)
                            if cyrillic_transition:
                                eng_part = cyrillic_transition.group(1)
                                if not re.search(r'[А-Яа-яЁё]', eng_part):
                                    thought_text += "\n\n" + eng_part.strip() + cyrillic_transition.group(2)
                                    cleaned_text = cyrillic_transition.group(3).strip()
                                else:
                                    cleaned_text = last_para.strip()
                            else:
                                cleaned_text = last_para.strip()

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
