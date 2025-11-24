"""Treino supervisionado (behavior cloning) da política neural com early stopping."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Optional

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader
except ImportError as exc:  # pragma: no cover - só avaliado quando torch não existe
    torch = None
    nn = None  # type: ignore[assignment]
    optim = None  # type: ignore[assignment]
    DataLoader = None  # type: ignore[assignment]
    _TORCH_IMPORT_ERROR = exc

from .agent import SudokuNet
from .data import build_dataloader


def _require_torch() -> None:
    if torch is None:
        raise ImportError(
            "torch é obrigatório para treinar a política neural "
            f"(erro original: {_TORCH_IMPORT_ERROR})"
        )


def _select_device(preferred: str = "cpu") -> "torch.device":
    """Escolhe o device: GPU se disponível, senão fallback."""
    _require_torch()
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():  # type: ignore[attr-defined]
        return torch.device("mps")
    return torch.device(preferred)


def _flatten_logits_targets(
    logits: "torch.Tensor", target: "torch.Tensor"
) -> tuple["torch.Tensor", "torch.Tensor"]:
    # logits: (B, 9, 9, 9) -> (B*81, 9), target: (B, 9, 9) -> (B*81)
    flat_logits = logits.reshape(-1, 9)
    flat_target = target.reshape(-1) - 1  # ajusta rótulo 1..9 -> 0..8
    return flat_logits, flat_target


class EarlyStopper:
    """Controla paciência para interromper o treino quando não há melhora."""

    def __init__(self, patience: int = 3, min_delta: float = 0.0) -> None:
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.min_validation_loss = float("inf")

    def should_stop(self, validation_loss: float) -> bool:
        if validation_loss < self.min_validation_loss - self.min_delta:
            self.min_validation_loss = validation_loss
            self.counter = 0
            return False
        self.counter += 1
        return self.counter >= self.patience


def _validate(
    model: "torch.nn.Module",
    loader: DataLoader,
    criterion: "torch.nn.Module",
    device: "torch.device",
) -> float:
    model.eval()
    total_loss = 0.0
    batches = 0
    with torch.no_grad():
        for batch in loader:
            obs = batch["obs"].to(device)
            target = batch["target"].to(device)
            logits = model(obs)
            flat_logits, flat_target = _flatten_logits_targets(logits, target)
            loss = criterion(flat_logits, flat_target)
            total_loss += loss.item()
            batches += 1
    return total_loss / max(batches, 1)


def train_supervised(
    train_csv: str | Path,
    val_csv: str | Path,
    *,
    save_path: str | Path = "policy_pretrain.pth",
    batch_size: int = 64,
    lr: float = 1e-3,
    epochs: int = 50,
    patience: int = 5,
    max_train_rows: Optional[int] = 1_000_000,
    max_val_rows: Optional[int] = 50_000,
    train_start_row: int = 0,
    val_start_row: int = 0,
    device_name: str = "cpu",
    num_workers: int = 0,
    dropout_rate: float = 0.1,
) -> Path:
    """Treina a rede com validação e early stopping."""
    _require_torch()
    device = _select_device(device_name)
    print(f"🚀 Treino em: {device} | Paciência: {patience} épocas")

    train_loader: DataLoader = build_dataloader(
        train_csv,
        batch_size=batch_size,
        max_rows=max_train_rows,
        start_row=train_start_row,
        num_workers=num_workers,
    )
    val_loader: DataLoader = build_dataloader(
        val_csv,
        batch_size=batch_size,
        max_rows=max_val_rows,
        start_row=val_start_row,
        num_workers=num_workers,
    )
    model = SudokuNet(dropout_rate=dropout_rate).to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    stopper = EarlyStopper(patience=patience)

    best_val_loss = float("inf")
    start = time.time()
    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        batches = 0
        epoch_start = time.time()

        for batch in train_loader:
            obs = batch["obs"].to(device)
            target = batch["target"].to(device)

            optimizer.zero_grad()
            logits = model(obs)
            flat_logits, flat_target = _flatten_logits_targets(logits, target)
            loss = criterion(flat_logits, flat_target)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            batches += 1

        avg_train_loss = total_loss / max(batches, 1)
        avg_val_loss = _validate(model, val_loader, criterion, device)

        print(
            f"Epoch {epoch+1}/{epochs} | "
            f"Train Loss: {avg_train_loss:.4f} | "
            f"Val Loss: {avg_val_loss:.4f} | "
            f"Time: {time.time() - epoch_start:.1f}s"
        )

        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), save_path)
            print(f"   ✅ Melhor modelo salvo (Loss: {best_val_loss:.4f})")

        if stopper.should_stop(avg_val_loss):
            print(f"🛑 Early stopping na época {epoch+1}")
            break

    print(f"⏱️ Tempo total: {time.time() - start:.2f}s")
    return Path(save_path)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Treino supervisionado (behavior cloning)")
    parser.add_argument("--train-csv", type=str, default="data/rl_data/sudoku.csv")
    parser.add_argument("--val-csv", type=str, default="data/rl_data/val.csv")
    parser.add_argument("--save-path", type=str, default="policy_pretrain.pth")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--patience", type=int, default=5)
    parser.add_argument("--max-train-rows", type=int, default=1_000_000)
    parser.add_argument("--max-val-rows", type=int, default=50_000)
    parser.add_argument("--train-start-row", type=int, default=0)
    parser.add_argument("--val-start-row", type=int, default=0)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--dropout-rate", type=float, default=0.1)
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    train_supervised(
        args.train_csv,
        args.val_csv,
        save_path=args.save_path,
        batch_size=args.batch_size,
        lr=args.lr,
        epochs=args.epochs,
        patience=args.patience,
        max_train_rows=args.max_train_rows,
        max_val_rows=args.max_val_rows,
        train_start_row=args.train_start_row,
        val_start_row=args.val_start_row,
        num_workers=args.num_workers,
        dropout_rate=args.dropout_rate,
    )
