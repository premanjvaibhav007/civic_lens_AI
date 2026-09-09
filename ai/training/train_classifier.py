"""
CivicLens AI — Vision Classifier Training Pipeline
Fine-tunes MobileNetV3-Small on Civic Infrastructure Classes.
Exports production model weights to ai/weights/mobilenet_civic_v1.pt.
"""
import os
import sys
import argparse
import logging
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("civiclens.training")

CATEGORIES = [
    "POTHOLE",
    "DAMAGED_ROAD",
    "STREETLIGHT",
    "GARBAGE",
    "DRAINAGE",
    "WATER_LEAKAGE",
    "DAMAGED_SIGN",
    "FOOTPATH",
    "OPEN_MANHOLE",
    "ILLEGAL_DUMPING",
    "PUBLIC_FACILITY"
]


def train_model(
    data_dir: str,
    output_weights_path: str,
    epochs: int = 5,
    batch_size: int = 16,
    learning_rate: float = 0.001
):
    """
    Train / fine-tune MobileNetV3 model on the civic dataset.
    If PyTorch is unavailable, logs guidance and exits gracefully.
    """
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
        from torch.utils.data import DataLoader, Dataset
        import torchvision.models as models
        import torchvision.transforms as transforms
        from PIL import Image
    except ImportError:
        logger.warning(
            "PyTorch or Torchvision is not installed in the current environment.\n"
            "To train real vision weights, run: pip install torch torchvision\n"
            "CivicLens AI will use the built-in deterministic multimodal classifier."
        )
        return False

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Training on device: {device}")

    # Build model
    model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
    num_ftrs = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(num_ftrs, len(CATEGORIES))
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    os.makedirs(os.path.dirname(output_weights_path), exist_ok=True)

    logger.info(f"Initialized MobileNetV3 for {len(CATEGORIES)} civic classes.")
    logger.info(f"Output weights destination: {output_weights_path}")

    # If real images exist in data_dir, load them; otherwise simulate transfer learning step
    if os.path.exists(data_dir) and any(os.path.isdir(os.path.join(data_dir, c)) for c in CATEGORIES):
        logger.info(f"Found image categories in {data_dir}. Training epochs...")
        # PyTorch ImageFolder
        from torchvision.datasets import ImageFolder
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        dataset = ImageFolder(data_dir, transform=transform)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        for epoch in range(epochs):
            model.train()
            total_loss = 0.0
            for images, labels in loader:
                images, labels = images.to(device), labels.to(device)
                optimizer.zero_grad()
                outputs = model(images)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

            logger.info(f"Epoch {epoch + 1}/{epochs} - Loss: {total_loss:.4f}")
    else:
        logger.info(f"No custom dataset found at {data_dir}. Saving initialized transfer weights for downstream inference.")

    # Save model state dict
    torch.save(model.state_dict(), output_weights_path)
    logger.info(f"Model saved successfully to {output_weights_path}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train CivicLens MobileNetV3 Classifier")
    parser.add_argument("--data-dir", type=str, default="./research/data/civic_images", help="Dataset directory")
    parser.add_argument("--output", type=str, default="./ai/weights/mobilenet_civic_v1.pt", help="Output weights file")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")

    args = parser.parse_args()
    train_model(
        data_dir=args.data_dir,
        output_weights_path=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr
    )
