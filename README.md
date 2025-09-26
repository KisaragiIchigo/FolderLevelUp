# FolderLevelUp ©️2025 KisaragiIchigo

## Download

[https://github.com/KisaragiIchigo/FolderLevelUp/releases/tag/v0.1.0]

## 概要
**FolderLevelUp** は、指定した親フォルダ(A)配下のBフォルダ群について、  
各B内のCフォルダ **「中身だけ」** をB直下に一括で移動させるツールです。  
（Cフォルダ自体は残ります）

- 操作はGUIベース（PySide6）  
- プレビュー表示や競合解決モード、Undo/Redoに対応  
- Windows Explorerへの即時更新通知機能つき  

---

## 機能
- **ドラッグ＆ドロップ**で親フォルダを指定  
- **プレビュー表示**で処理前に確認可能  
- **競合解決モード**  
  - スキップ（同名があれば無視）  
  - 上書き（既存を削除して移動）  
  - 自動リネーム（`name_1`, `name_2` … を採番）  
- **Undo/Redo** で直前の移動を取り消し／やり直し  
- **ドライトランモード**（実際には移動せずシミュレーション）  

---

## 使い方
1. アプリを起動し、親フォルダ(A)を **ドラッグ＆ドロップ** する  
   （または「フォルダを選ぶ…」ボタンから指定）  
2. 左側ツリーで対象のB/Cフォルダを選択  
   - 複数選択可  
   - F2キーやゆっくりクリックでリネーム可  
3. 「選択からプレビュー生成」ボタンを押す  
4. 競合モードを選択（スキップ／上書き／自動リネーム）  
5. 必要なら「ドライトラン」にチェック  
6. 「移動を実行」で処理開始  

---

## スクリーンショット
（ここにGUI画面のキャプチャを貼ると分かりやすいです）

---

## サンプル構造

入力（Before）:
A/  
├─ B1/  
│ ├─ C1/  
│ │ ├─ file1.txt  
│ │ └─ file2.txt  
│ └─ C2/  
│ └─ file3.txt  
└─ B2/  
└─ C3/  
└─ file4.txt  

実行後（After）:
A/  
├─ B1/  
│ ├─ C1/  
│ ├─ C2/  
│ ├─ file1.txt  
│ ├─ file2.txt  
│ └─ file3.txt  
└─ B2/  
├─ C3/  
└─ file4.txt  

---



必要ライブラリ

- Python 3.9+ 推奨
- PySide6

  
ファイル構成  
FolderLevelUp/  
├── FolderLevelUp.py      # 起動用エントリポイント  
├── gui.py                # GUI（PySide6ベース）  
├── processor.py          # ディレクトリ走査・移動処理ロジック  
├── config.py             # 設定の保存/読み込み（JSON）  
├── utils.py              # QSSデザイン・Windows通知など  


ライセンス

© 2025 KisaragiIchigo
MITライセンス
