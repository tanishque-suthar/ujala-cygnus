import torchxrayvision as xrv
import torch

model = xrv.models.DenseNet(weights="densenet121-res224-all")
print("Model created.")
# generate dummy input in range [-1024, 1024]
dummy_input = torch.randn(1, 1, 224, 224) * 1024
output = model(dummy_input)
print("Output:", output)
