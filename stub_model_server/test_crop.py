import torchxrayvision as xrv
from PIL import Image
import numpy as np
import torchvision
import io
import sys

image = Image.open("/home/tsvd/Desktop/projects/cygnus-densenet-migration/person1_bacteria_1.jpeg")
print("Original size:", image.size)

img = np.array(image.convert("L"), dtype=np.float32)
img = xrv.datasets.normalize(img, 255)
img = img[None, :, :]

transform = torchvision.transforms.Compose([
    xrv.datasets.XRayCenterCrop(),
    xrv.datasets.XRayResizer(224),
])

img_t = transform(img)

# Save output to see if it's letterboxed
from matplotlib import pyplot as plt
plt.imsave("test_out.png", img_t[0], cmap="gray")
