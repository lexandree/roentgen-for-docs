import io
from PIL import Image

class ImageProcessor:
    TARGET_SIZE = 896
    
    @staticmethod
    def process_main_image(image_bytes: bytes) -> bytes:
        """
        Creates a square center crop of the original image to prevent 
        distortion when the inference worker scales it to a square, 
        and resizes it to the target resolution.
        """
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = img.size
        
        # Determine the shortest side to make a maximal square crop
        shortest_side = min(w, h)
        left = (w - shortest_side) // 2
        top = (h - shortest_side) // 2
        right = left + shortest_side
        bottom = top + shortest_side
        
        # Center crop
        img = img.crop((left, top, right, bottom))
        
        # Resize to 896x896
        img = img.resize((ImageProcessor.TARGET_SIZE, ImageProcessor.TARGET_SIZE), Image.LANCZOS)
        
        out_io = io.BytesIO()
        img.save(out_io, format="JPEG", quality=95)
        return out_io.getvalue()
        
    @staticmethod
    def process_roi_image(image_bytes: bytes, preset: str) -> bytes:
        """
        Extracts a specific Region of Interest (ROI), crops it into a square,
        and resizes it to the target resolution for detailed analysis.
        """
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = img.size
        
        # The crop window size is 50% of the shortest side to provide significant zoom
        crop_size = min(w, h) // 2
        
        # Define logical centers for presets
        centers = {
            "top_left": (w // 4, h // 4),
            "top_right": (3 * w // 4, h // 4),
            "center": (w // 2, h // 2),
            "bottom_left": (w // 4, 3 * h // 4),
            "bottom_right": (3 * w // 4, 3 * h // 4),
        }
        
        cx, cy = centers.get(preset, centers["center"])
        
        # Calculate initial bounding box
        left = cx - crop_size // 2
        top = cy - crop_size // 2
        right = left + crop_size
        bottom = top + crop_size
        
        # Clamp bounding box to image dimensions
        if left < 0:
            left = 0
            right = crop_size
        if top < 0:
            top = 0
            bottom = crop_size
        if right > w:
            right = w
            left = w - crop_size
        if bottom > h:
            bottom = h
            top = h - crop_size
            
        # Extract the region
        roi_img = img.crop((left, top, right, bottom))
        
        # Resize to 896x896
        roi_img = roi_img.resize((ImageProcessor.TARGET_SIZE, ImageProcessor.TARGET_SIZE), Image.LANCZOS)
        
        out_io = io.BytesIO()
        roi_img.save(out_io, format="JPEG", quality=95)
        return out_io.getvalue()

image_processor = ImageProcessor()
