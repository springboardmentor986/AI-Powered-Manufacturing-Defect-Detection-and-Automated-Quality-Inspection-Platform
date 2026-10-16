from preprocess import preprocess_image

image_path = "uploads/Screenshot 2026-06-08 131046.png"

image = preprocess_image(image_path)

print("Preprocessing successful!")
print("Image shape:", image.shape)
print("Minimum pixel value:", image.min())
print("Maximum pixel value:", image.max())