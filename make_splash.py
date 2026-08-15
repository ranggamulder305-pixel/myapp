from PIL import Image

img = Image.new('RGB', (1200, 600), color='#1a1a2e')
img.save('data/presplash.png')
print("✓ Presplash created!")
