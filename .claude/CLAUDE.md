# CLAUDE.md

このファイルは Claude Code がこのディレクトリで作業する際のガイドラインです。

## sandbox/ について

このディレクトリは実験・検証用のワークスペースです。

- **目的**: 新しい技術やライブラリの検証、プロトタイプの作成、アイデアの試行
- **Git管理**: 初期化済み（`git init` 実行済み）
- **自由度**: 破壊的な変更や実験的なコードも歓迎

## 利用言語・ツール

### Python

- **パッケージマネージャー**: [uv](https://github.com/astral-sh/uv) - Astral製の高速Pythonパッケージマネージャー
- **Linter/Formatter**: [ruff](https://github.com/astral-sh/ruff) - 高速なPython linter/formatter
- **型チェッカー**: [ty](https://github.com/astral-sh/ty) - Astral製の型チェッカー

### 開発ワークフロー

```bash
# 依存関係のインストール（lockファイル基準、意図しないバージョンアップを防止）
uv sync

# lockファイルの更新（pyproject.tomlの変更を反映）
uv lock

# 依存関係を最新バージョンに更新したい場合のみ
uv sync --upgrade

# コードフォーマット
uv run ruff format .

# Lint実行
uv run ruff check .

# 型チェック
uv run ty check

# Pre-commit hooks実行
pre-commit run --all-files
```

**重要:** `uv sync`はデフォルトで`uv.lock`を基準にインストールします。意図しないバージョンアップを防ぐため、通常は`uv sync`のみを使用し、明示的にアップグレードしたい場合のみ`--upgrade`フラグを使用してください。
