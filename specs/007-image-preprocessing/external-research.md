Вопрос: у меня микросервисная архитектура бот телеграм - диспетчер с БД и управлением сессиями - воркер (в частности llama-server на GTX 1060 6GB). Medgemma 1.5 известна своей капризностью к построению и управлению структурой диалога. В файлах собраны предварительные соображения, логи запуска воркера и часть исходников. В принципе всё работает. 

3. Требуется стратегия подготовки изображений crop, zoom, compare 2 images или что то еще.
4. При подключении воркеров на арендованных мощностях с VRAM 24/48/etc GB имеем расширенные возможности улучшения функционала, например анализ серий изображений от 3D сканирования - стратегия подготовки и реализация



## 3. Стратегия подготовки изображений

MedGemma обрабатывает изображения в 896×896. Это определяет всю стратегию.

```python
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import io, base64

def prepare_xray(image_path: str, mode: str = "single") -> str:
    """
    mode: "single" | "crop_roi" | "windowed" | "compare"
    """
    img = Image.open(image_path).convert("RGB")
    
    if mode == "single":
        # Простое масштабирование с сохранением пропорций + padding
        result = letterbox_resize(img, 896)
        
    elif mode == "crop_roi":
        # Авто-кроп: убираем края рентгена (маркеры, рамки)
        # Обычно ROI — центральные 85% по ширине, 90% по высоте
        w, h = img.size
        margin_x = int(w * 0.075)
        margin_y = int(h * 0.05)
        cropped = img.crop((margin_x, margin_y, w - margin_x, h - margin_y))
        result = letterbox_resize(cropped, 896)
        
    elif mode == "windowed":
        # Улучшение контраста для выявления патологий
        # Особенно полезно для лёгочного рисунка
        arr = np.array(img.convert("L"), dtype=np.float32)
        p2, p98 = np.percentile(arr, [2, 98])
        arr = np.clip((arr - p2) / (p98 - p2) * 255, 0, 255).astype(np.uint8)
        enhanced = Image.fromarray(arr).convert("RGB")
        result = letterbox_resize(enhanced, 896)
        
    elif mode == "compare":
        # Два изображения side-by-side в одном 896x448 каждое
        # Передаётся как ОДНО изображение 896x896
        raise ValueError("Use prepare_comparison() for two images")
    
    return image_to_b64(result)


def prepare_comparison(img_path_1: str, img_path_2: str, 
                        label1: str = "До", label2: str = "После") -> str:
    """
    Создаёт side-by-side: два снимка в одном изображении 896x896.
    Модель видит одно изображение, но промпт описывает структуру.
    """
    from PIL import ImageDraw, ImageFont
    
    img1 = letterbox_resize(Image.open(img_path_1).convert("RGB"), 448, height=896)
    img2 = letterbox_resize(Image.open(img_path_2).convert("RGB"), 448, height=896)
    
    combined = Image.new("RGB", (896, 896), (0, 0, 0))
    combined.paste(img1, (0, 0))
    combined.paste(img2, (448, 0))
    
    # Разделительная линия
    draw = ImageDraw.Draw(combined)
    draw.line([(447, 0), (447, 896)], fill=(200, 200, 200), width=2)
    
    # Метки (опционально)
    draw.text((10, 10), label1, fill=(255, 255, 0))
    draw.text((458, 10), label2, fill=(255, 255, 0))
    
    return image_to_b64(combined)


def letterbox_resize(img: Image.Image, width: int, height: int = None) -> Image.Image:
    if height is None:
        height = width
    img.thumbnail((width, height), Image.LANCZOS)
    result = Image.new("RGB", (width, height), (0, 0, 0))
    offset = ((width - img.width) // 2, (height - img.height) // 2)
    result.paste(img, offset)
    return result


def image_to_b64(img: Image.Image) -> str:
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=92)
    return base64.b64encode(buffer.getvalue()).decode()
```

**Промпт для сравнения двух снимков:**

```python
COMPARE_TASK = """На изображении два рентгеновских снимка side-by-side.
ЛЕВЫЙ снимок: {label1}
ПРАВЫЙ снимок: {label2}

Сравни оба снимка. Опиши:
1. Изменения в динамике (что улучшилось / ухудшилось / без изменений)
2. Новые патологические находки на правом снимке
3. Регрессировавшие находки
4. Вывод о динамике лечения"""
```

---

## 4. Стратегия для арендованных мощностей (24/48 GB VRAM)

На 24+ GB полностью меняется игра. Пример для A10G (24 GB) или A100 (40/80 GB):

```bash
# A10G 24GB — оптимальный запуск
./llama-server \
  -m models/medgemma-1.5-4b.gguf \
  --mmproj models/mmproj-model-f16.gguf \
  -ngl -1 \
  -c 32768 \       # 32k токенов — достаточно для серии из ~15-20 снимков
  -np 8 \          # 8 параллельных слотов
  --port 8002 \
  --chat-template gemma \
  --jinja \
  -tb 16           # batch threads
```

**Стратегия обработки CT/MRI серий:**

```python
class CTSeriesProcessor:
    """
    Стратегия для серий из 3D-сканирования.
    CT грудной клетки: обычно 200-400 срезов.
    Нельзя отправить все — нужна умная выборка.
    """
    
    def select_key_slices(self, series_paths: list, strategy: str = "uniform") -> list:
        """
        Стратегии выборки срезов:
        - uniform: равномерно N срезов из серии
        - apex_base: верхушки лёгких + основания + середина (для пульмонологии)  
        - pathology_focused: если известна зона — срезы через неё
        """
        n = len(series_paths)
        
        if strategy == "uniform":
            # 9 срезов: 3 верхних, 3 средних, 3 нижних
            indices = [int(n * i / 8) for i in range(9)]
            return [series_paths[i] for i in indices]
            
        elif strategy == "apex_base":
            # Специфично для лёгких
            zones = {
                "apex": range(int(n * 0.05), int(n * 0.20)),    # верхушки 
                "upper": range(int(n * 0.20), int(n * 0.40)),   # верхние доли
                "middle": range(int(n * 0.40), int(n * 0.60)),  # средние доли
                "lower": range(int(n * 0.60), int(n * 0.80)),   # нижние доли
                "base": range(int(n * 0.80), int(n * 0.95)),    # основания
            }
            selected = []
            for zone_name, zone_range in zones.items():
                zone_list = list(zone_range)
                # Берём 2 репрезентативных среза из каждой зоны
                mid = zone_list[len(zone_list) // 2]
                selected.extend([series_paths[mid - 1], series_paths[mid]])
            return selected  # 10 срезов
    
    def build_series_grid(self, slice_paths: list, grid: str = "3x3") -> str:
        """
        Собирает grid из срезов в одно изображение 896x896.
        3x3 = 9 срезов по 298x298 пикселей каждый.
        """
        cols, rows = map(int, grid.split("x"))
        cell_w = 896 // cols
        cell_h = 896 // rows
        
        canvas = Image.new("RGB", (896, 896), (0, 0, 0))
        
        for i, path in enumerate(slice_paths[:cols * rows]):
            row, col = divmod(i, cols)
            slice_img = letterbox_resize(
                Image.open(path).convert("RGB"), 
                cell_w, cell_h
            )
            canvas.paste(slice_img, (col * cell_w, row * cell_h))
            
            # Номер среза в углу
            draw = ImageDraw.Draw(canvas)
            draw.text(
                (col * cell_w + 3, row * cell_h + 3), 
                str(i + 1), 
                fill=(255, 255, 0)
            )
        
        return image_to_b64(canvas)
    
    async def analyze_series(
        self, 
        series_paths: list, 
        user_type: str,
        llama_url: str
    ) -> dict:
        """
        Двухэтапный анализ:
        1. Grid-overview: общая картина по 9 срезам
        2. Targeted: детальный анализ зон с находками
        """
        key_slices = self.select_key_slices(series_paths, strategy="apex_base")
        grid_b64 = self.build_series_grid(key_slices, grid="3x3")
        
        overview_task = """На изображении сетка из 9 срезов CT в порядке сверху-вниз.
Срезы пронумерованы 1-9 (1=верхушки, 9=основания лёгких).

Проведи обзорный анализ:
1. Общая характеристика паренхимы
2. Номера срезов с патологическими находками (если есть)
3. Предварительная оценка распространённости процесса
4. Рекомендация: какие зоны требуют детального анализа"""
        
        # Этап 1
        overview_resp = await self._send_request(
            llama_url, grid_b64, user_type, overview_task
        )
        
        return {
            "overview": overview_resp,
            "slices_analyzed": len(key_slices),
            "total_slices": len(series_paths)
        }
```

**Сравнение возможностей по конфигурациям:**

| Параметр | GTX 1060 6GB | A10G 24GB | A100 40GB |
|---|---|---|---|
| Контекст | 6144 | 32768 | 65536 |
| Слоты `-np` | 2 | 8 | 16 |
| Изображений за запрос | 1 | 3–4 | 6–9 |
| CT серия (срезов) | нет | 9 (grid) | 16–25 |
| Параллельных пользователей | 1–2 | 6–8 | 12–16 |

---

## Итоговая архитектура

```
Telegram Bot
     │
     ▼
Dispatcher (FastAPI)
  ├── Session Manager (Redis/PostgreSQL)
  ├── Image Preprocessor
  │     ├── single/crop/windowed/compare
  │     └── CT series grid builder
  ├── Slot Router
  │     ├── slot 0 → radiologist  
  │     └── slot 1 → patient
  └── Worker Client (httpx)
         │
         ▼
   llama-server
   -np 2 -c 6144
   cache_prompt: true
```

Запустите прогрев слотов при старте диспетчера через `warmup_slots()` — это даст ощутимое снижение латентности уже на первых реальных запросах.



Вопрос: llama-server вроде самостоятельно делает resize 896x896 искажая неквадратные изображения. Т.е. видимо оптимальнее вырезать такое окно из изображения? Но возникает вопрос - обучали medgemma на обрезанных или уменьшенных изображениях. очевидно, что эффективность будет зависеть от степени приближения к виду тренировочных данных. Так же и с разрешающей способностью в 14 пикселей - будет ли польза в повышении разрешения выбранного региона или вырезка окна 896x896 из изображения высокого разрешения приведет к худшим результатам чем уменьшение изобоажения?

Ответ: Отличный вопрос — это действительно один из самых важных нюансов для качества работы MedGemma.

## Как llama-server обрабатывает изображения

В `clip.cpp` llama.cpp делает прямой bilinear resize до 896×896 **без сохранения aspect ratio**. Для портретного рентгена (типичное соотношение ~3:4 или 2:3) это означает горизонтальное сжатие ~15–25%. Клинически это критично — искажается ширина медиастинума, кардиоторакальный индекс, форма куполов диафрагмы.

Вывод: **нужно всегда отдавать серверу уже готовый квадратный 896×896, подготовленный на стороне диспетчера**.

---

## Чем обучали MedGemma — что известно

MedGemma использует SigLIP-400M энкодер. Стандартный SigLIP preprocessing в обучении Google:

```
1. Resize: shortest side → 896px (сохранение aspect ratio)
2. Center crop: 896×896 из результата
```

Для chest X-ray датасетов (CheXpert, MIMIC-CXR) исходные изображения обычно ~2500×3000 px, портретные. После SigLIP-preprocessing модель видела **весь снимок, слегка обрезанный по бокам**, но без искажений пропорций.

Это означает:
- Модель **не видела** чёрные padding-полосы от letterbox
- Модель **видела** небольшие crop-артефакты по краям
- Сильное растяжение/сжатие → **вне дистрибуции обучения**

---

## Главный вопрос: crop окна vs resize

Здесь зависит от задачи и размера исходного изображения.

```python
import numpy as np
from PIL import Image
import io, base64

def analyze_xray_resolution(img: Image.Image) -> dict:
    """Что происходит с деталями при разных стратегиях."""
    w, h = img.size
    
    # Стратегия A: resize всего изображения
    scale_factor = 896 / max(w, h)
    effective_px_per_patch_A = (1 / scale_factor) * 14  # оригинальных пикселей на патч
    
    # Стратегия B: crop центрального окна 896x896
    # (только если изображение >= 896x896)
    if w >= 896 and h >= 896:
        effective_px_per_patch_B = 14  # 1:1 маппинг
    else:
        effective_px_per_patch_B = None  # апскейл — хуже
    
    return {
        "original": f"{w}x{h}",
        "patches_per_side": 64,  # 896/14 = 64
        "strategy_A_px_per_patch": round(effective_px_per_patch_A, 1),
        "strategy_B_px_per_patch": effective_px_per_patch_B,
        "advice": "crop" if (w >= 2048 or h >= 2048) else "resize"
    }

# Пример для типичного рентгена 2048x2500:
# strategy_A: каждый патч покрывает ~36x36 оригинальных пикселей
# strategy_B: каждый патч покрывает 14x14 оригинальных пикселей → в 6.6x лучше детализация
```

**Но проблема crop-стратегии** — анатомический контекст:

```
Рентген грудной клетки 2048x2500
При crop 896x896 центрального окна:
  - видим только ~44% ширины грудной клетки
  - теряем периферию лёгких, рёбра, оба синуса
  - модель не может оценить кардиоторакальный индекс
  - пневмоторакс по краю = невидим
```

---

## Правильная стратегия в зависимости от задачи

```python
from PIL import Image, ImageDraw
import numpy as np
import io, base64
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class PreparedImage:
    b64: str
    strategy: str
    notes: str  # что передать в промпт

def prepare_for_medgemma(
    img_path: str,
    task: str = "full_chest",
    roi: Optional[Tuple[int,int,int,int]] = None  # x1,y1,x2,y2
) -> PreparedImage:
    img = Image.open(img_path).convert("RGB")
    w, h = img.size
    
    if task == "full_chest":
        return _prepare_full_chest(img)
    
    elif task == "roi_detail" and roi:
        return _prepare_roi(img, roi)
    
    elif task == "two_stage_roi":
        # Сначала диспетчер делает full_chest для обзора,
        # затем по ответу модели делает roi_detail
        return _prepare_full_chest(img)


def _prepare_full_chest(img: Image.Image) -> PreparedImage:
    """
    Оптимально для обзорного анализа.
    SigLIP-стиль: сохраняем aspect ratio, минимальный crop.
    """
    w, h = img.size
    target = 896
    
    # Масштабируем по короткой стороне → crop центра (как в обучении)
    scale = target / min(w, h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    
    # Center crop 896x896
    left = (new_w - target) // 2
    top = (new_h - target) // 2
    cropped = resized.crop((left, top, left + target, top + target))
    
    # Что потеряли? Предупреждаем в промпте
    crop_fraction_w = target / new_w
    crop_fraction_h = target / new_h
    lost_edges = crop_fraction_w < 0.98 or crop_fraction_h < 0.98
    
    return PreparedImage(
        b64=_to_b64(cropped),
        strategy="siglip_center_crop",
        notes="Изображение обрезано по краям ~{:.0f}% для сохранения пропорций.".format(
            (1 - min(crop_fraction_w, crop_fraction_h)) * 100
        ) if lost_edges else ""
    )


def _prepare_roi(img: Image.Image, roi: Tuple[int,int,int,int]) -> PreparedImage:
    """
    Детальный анализ зоны интереса.
    Используем ТОЛЬКО если исходник >= 1500px по короткой стороне.
    """
    x1, y1, x2, y2 = roi
    w, h = img.size
    target = 896
    
    roi_w = x2 - x1
    roi_h = y2 - y1
    
    # Важно: если ROI маленький, добавляем контекст вокруг него
    # Минимум: ROI должен быть > 50% от итогового кадра
    context_factor = 1.5  # расширяем ROI на 50% для контекста
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    half_size = int(max(roi_w, roi_h) * context_factor / 2)
    
    # Квадратное окно с контекстом
    nx1 = max(0, cx - half_size)
    ny1 = max(0, cy - half_size)
    nx2 = min(w, cx + half_size)
    ny2 = min(h, cy + half_size)
    
    cropped = img.crop((nx1, ny1, nx2, ny2))
    
    # Масштабируем до 896x896
    # Если cropped >= 896 → downscale (детализация лучше чем у full_chest)
    # Если cropped < 896 → upscale → ХУЖЕ чем full_chest, использовать с осторожностью
    result = cropped.resize((target, target), Image.LANCZOS)
    
    upscaled = cropped.width < target or cropped.height < target
    scale_ratio = target / min(cropped.width, cropped.height)
    
    notes = f"Увеличенный регион интереса ({cropped.width}×{cropped.height}px → 896×896)."
    if upscaled:
        notes += " ВНИМАНИЕ: апскейл, детализация ограничена."
    
    return PreparedImage(
        b64=_to_b64(result),
        strategy="roi_zoom",
        notes=notes
    )


def _to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return base64.b64encode(buf.getvalue()).decode()
```

---

## Ответ на вопрос об апскейле

```
Исходник 512x512 → crop 896x896 окна → невозможно (источник меньше)
Исходник 512x512 → resize до 896x896 → апскейл x1.75

Что видит модель при апскейле:
  - "размытые" патчи (интерполированные пиксели)
  - модель обучена на реальных медицинских изображениях
  - апскейлнутые изображения = другое статистическое распределение
  - результат: менее уверенные ответы, больше галлюцинаций

Правило: никогда не апскейлить для MedGemma.
Если исходник < 896px → resize до 896 с letterbox лучше чем апскейл ROI.
```

---

## Двухэтапный pipeline (рекомендуемый)

```python
async def two_stage_analysis(img_path: str, user_type: str) -> dict:
    """
    Этап 1: Обзорный анализ всего снимка
    Этап 2: Если модель указала зоны → детальный анализ ROI
    """
    
    # Этап 1: full chest
    prep = prepare_for_medgemma(img_path, task="full_chest")
    
    stage1_task = """Проведи обзорный анализ.
В конце отчёта добавь секцию:
ZONES_FOR_DETAIL: [перечисли зоны требующие детального анализа в формате: 
left_upper / left_lower / right_upper / right_lower / mediastinum / none]"""
    
    stage1_result = await send_to_llama(prep.b64, stage1_task, user_type)
    
    # Парсим зоны из ответа
    zones = parse_zones(stage1_result["report"])
    
    if not zones or "none" in zones:
        return {"stage1": stage1_result, "stage2": None}
    
    # Этап 2: детальный анализ зон (только если исходник высокого разрешения)
    img = Image.open(img_path)
    w, h = img.size
    
    if min(w, h) < 1500:
        # Апскейл бессмысленен
        return {"stage1": stage1_result, "stage2": "low_res_source"}
    
    stage2_results = {}
    for zone in zones:
        roi = get_zone_coords(zone, w, h)  # анатомические координаты зоны
        prep2 = prepare_for_medgemma(img_path, task="roi_detail", roi=roi)
        
        stage2_task = f"""Детальный анализ зоны: {zone}.
Предыдущий обзор показал патологию в этой зоне.
Опиши максимально детально: размер, края, плотность, связь с окружающими структурами."""
        
        stage2_results[zone] = await send_to_llama(prep2.b64, stage2_task, user_type)
    
    return {"stage1": stage1_result, "stage2": stage2_results}


def get_zone_coords(zone: str, w: int, h: int) -> Tuple[int,int,int,int]:
    """Анатомические зоны рентгена грудной клетки."""
    zones = {
        "right_upper": (int(w*0.5), 0,          w,         int(h*0.4)),
        "right_lower": (int(w*0.5), int(h*0.4), w,         h),
        "left_upper":  (0,          0,           int(w*0.5), int(h*0.4)),
        "left_lower":  (0,          int(h*0.4), int(w*0.5), h),
        "mediastinum": (int(w*0.35), int(h*0.1), int(w*0.65), int(h*0.8)),
    }
    return zones.get(zone, (0, 0, w, h))
```

---

## Резюме

| Стратегия | Когда использовать | Детализация | Контекст |
|---|---|---|---|
| SigLIP center crop | Всегда для обзора, исходник любой | Средняя | Полный |
| ROI zoom (downscale) | Исходник ≥1500px, есть целевая зона | Высокая | Частичный |
| ROI zoom (upscale) | Никогда | Хуже чем center crop | Частичный |
| Letterbox | Только если боитесь потерять края | Средняя | Полный |
| Прямой stretch | Никогда для рентгена | Средняя | Искажён |

Главный вывод: **всегда предобрабатывайте до 896×896 на стороне диспетчера**, используйте SigLIP center crop как базовую стратегию, и добавляйте второй этап с ROI только при высококачественных исходниках.