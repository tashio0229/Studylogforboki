# Studylogforboki - パーソナル秘書システム

ベステラ株式会社 経理財務課向けのAIパーソナル秘書システムです。
[cc-secretary](https://github.com/Shin-sibainu/cc-secretary) をベースに、経理財務業務に最適化しています。

## 使い方

### 日常の管理

Claude Code で以下のコマンドを入力するだけ:

```
/secretary
```

`.secretary/` フォルダが検出されると管理モードが起動し、以下の操作ができます:

| コマンド | 動作 |
|---------|------|
| タスク追加 [内容] | 今日のTODOにタスクを追加 |
| 今日のタスク | 今日のタスクを表示 |
| メモ [内容] | inboxにクイックキャプチャ |
| 調査 [タイトル] | リサーチファイルを新規作成 |
| 週次レビュー | 週次レビューを自動生成 |
| ダッシュボード | 全体概要を表示 |
| 受信箱整理 | inboxの整理を支援 |

## フォルダ構成

```
.secretary/
├── CLAUDE.md        # 個人設定・プロフィール
├── inbox/           # クイックキャプチャ（迷ったらここへ）
├── reviews/         # 週次・月次レビュー
├── todos/           # デイリータスク管理
├── meetings/        # 議事録・ミーティングメモ
├── projects/        # プロジェクト管理
├── finances/        # 財務・経理記録
├── research/        # 調査・リサーチ
├── knowledge/       # ナレッジベース
└── clients/         # 取引先管理
```

## プラグインとして使う（オプション）

このリポジトリを Claude Code プラグインとしてインストールすることもできます:

```
/plugin marketplace add tashio0229/Studylogforboki
/plugin install secretary@studylogforboki-secretary
```

## ライセンス

MIT
