
from PIL import Image
import os

img_path = r"C:/Users/SRV/.gemini/antigravity/brain/742d7d3a-3369-42fa-90cc-9a80c140c97d/uploaded_image_1765675677200.png"
save_path = "icon.ico"

try:
    img = Image.open(img_path)
    img.save(save_path, format='ICO', sizes=[(256, 256)])
    print(f"Icon saved to {os.path.abspath(save_path)}")
except Exception as e:
    print(f"Error: {e}")
