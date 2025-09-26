
import os
from typing import List
from PySide6.QtCore import Qt, QEvent, QPoint, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem, QSplitter,
    QMessageBox, QCheckBox, QComboBox, QProgressBar, QAbstractItemView,
    QDialog, QDialogButtonBox, QTextEdit
)

from processor import (
    scan_structure, build_preview, execute_operations,
    ConflictMode, MoveRecord
)
from utils import set_app_icon_if_exists, app_qss, save_window_state, load_window_state
from utils import shell_notify_rename
from config import Config

APP_TITLE = "FolderLevelUp ©️2025 KisaragiIchigo"
RESIZE_MARGIN = 8

# README本文
README_TEXT = """# FolderLevelUp - README

## このツールでできること
指定した親フォルダ（A）の直下にある子フォルダ（B）を対象に、  
その中のさらに下のフォルダ（C）の **「中身だけ」** をB直下へ1階層上げます。  
※Cフォルダそのものは残ります。

---

## 基本的な使い方
1. 親フォルダ A を指定する  
   - ドラッグ＆ドロップ  
   - または［フォルダを選ぶ…］から指定
2. 左のツリーで対象フォルダを選ぶ（複数可）  
   - F2キーで名前変更も可能
3. ［選択からプレビュー生成］をクリック
4. 衝突時の動作を選択（スキップ / 上書き / 自動リネーム）
5. 必要なら［ドライトラン］をONにして確認
6. 問題なければ［移動を実行］

---

## 衝突モードの説明
- **スキップ**：同名のファイル・フォルダがあれば移動しない
- **上書き**：既存のものを削除してから移動
- **自動リネーム**：同名があれば `name_1`, `name_2` … と自動採番して移動

---

## ヒントと便利機能
- プレビューで結果を確認してから実行できるので安心
- 進捗バーや完了ダイアログで状態をチェック可能
- Undo / Redo 対応  
  - Undo：直前の実行を取り消す  
  - Redo：取り消した操作をやり直す

"""

class DropLabel(QLabel):
    def __init__(self, on_path_dropped, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._on_dropped = on_path_dropped
        self.setText("ここに【親フォルダ A】をドラッグ＆ドロップ\nまたは下の［フォルダを選ぶ］から指定")
        self.setAlignment(Qt.AlignCenter)
        self.setObjectName("dropArea")
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            for u in e.mimeData().urls():
                p = u.toLocalFile()
                if os.path.isdir(p):
                    e.acceptProposedAction(); return
    def dropEvent(self, e):
        files = [u.toLocalFile() for u in e.mimeData().urls()]
        dirs = [p for p in files if os.path.isdir(p)]
        if dirs: self._on_dropped(dirs[0])

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(1000, 680)
        set_app_icon_if_exists(self)  

        self._moving = False
        self._resizing = False
        self._drag_offset = QPoint()
        self._resize_edges = ""
        self._config = Config.load()  # 設定ロード（最後のAフォルダ、ウィンドウ位置など）
        self._last_A = self._config.last_root or ""

        self.setStyleSheet(app_qss())  

        outer = QVBoxLayout(self); outer.setContentsMargins(8,8,8,8); outer.setSpacing(8)
        bg = QWidget(); bg.setObjectName("bgRoot"); outer.addWidget(bg)
        lay = QVBoxLayout(bg); lay.setContentsMargins(10,10,10,10); lay.setSpacing(8)
        card = QWidget(); card.setObjectName("glassRoot"); lay.addWidget(card)
        main = QVBoxLayout(card); main.setContentsMargins(14,14,14,14); main.setSpacing(8)

        # ===== タイトルバー =====
        title_row = QHBoxLayout()
        self.lbl_title = QLabel("FolderLevelUp")
        self.lbl_title.setObjectName("titleLabel")

        # READMEボタン
        btn_readme = QPushButton("README")
        btn_readme.setToolTip("READMEを開く")
        btn_readme.clicked.connect(self._show_readme_dialog)

        # ウィンドウ制御（順序：最小化 → 最大化/復元 → 閉じる）
        btn_min  = QPushButton("🗕"); btn_min.setObjectName("minBtn");  btn_min.setFixedSize(28,28); btn_min.clicked.connect(self.showMinimized)
        self.btn_max = QPushButton("🗖"); self.btn_max.setObjectName("maxBtn"); self.btn_max.setFixedSize(28,28); self.btn_max.clicked.connect(self._toggle_max)
        btn_close = QPushButton("ｘ"); btn_close.setObjectName("closeBtn"); btn_close.setFixedSize(28,28); btn_close.clicked.connect(self.close)

        title_row.addWidget(self.lbl_title)
        title_row.addStretch()
        title_row.addWidget(btn_readme)  
        title_row.addWidget(btn_min)
        title_row.addWidget(self.btn_max)
        title_row.addWidget(btn_close)
        main.addLayout(title_row)

        # ===== A 選択 =====
        self.drop = DropLabel(self._on_root_dropped); self.drop.setFixedHeight(84); main.addWidget(self.drop)
        btn_row = QHBoxLayout()
        self.btn_choose = QPushButton("フォルダを選ぶ…"); self.btn_choose.clicked.connect(self._choose_root)
        self.chk_include_hidden = QCheckBox("隠し要素を含める"); self.chk_include_hidden.setChecked(False)
        self.chk_simulate = QCheckBox("ドライトラン（実際には移動しない）"); self.chk_simulate.setChecked(False)
        btn_row.addWidget(self.btn_choose); btn_row.addStretch(); btn_row.addWidget(self.chk_include_hidden); btn_row.addWidget(self.chk_simulate)
        main.addLayout(btn_row)

        # ===== 左右 =====
        splitter = QSplitter()
        # 左：ツリー
        left_panel = QWidget(); l = QVBoxLayout(left_panel); l.setContentsMargins(0,0,0,0); l.setSpacing(6)
        self.tree = QTreeWidget(); self.tree.setHeaderLabels(["フォルダ", "パス"]); self.tree.setColumnWidth(0, 300)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # ★ F2/ゆっくりクリックで編集可能
        self.tree.setEditTriggers(QAbstractItemView.EditKeyPressed | QAbstractItemView.SelectedClicked | QAbstractItemView.EditKeyPressed)
        self.tree.itemChanged.connect(self._on_tree_item_changed)
        l.addWidget(QLabel("B→C ツリー（Ctrl/Shiftで複数選択 / F2で名称変更）"))

        sel_row = QHBoxLayout()
        self.btn_refresh_tree = QPushButton("更新"); self.btn_refresh_tree.clicked.connect(self._rescan)
        self.btn_clear_preview_left = QPushButton("リストクリア"); self.btn_clear_preview_left.clicked.connect(self._clear_preview)
        sel_row.addWidget(self.btn_refresh_tree); sel_row.addWidget(self.btn_clear_preview_left); sel_row.addStretch()
        l.addLayout(sel_row)
        l.addWidget(self.tree, 1)

        # 右：プレビュー
        right_panel = QWidget(); r = QVBoxLayout(right_panel); r.setContentsMargins(0,0,0,0); r.setSpacing(6)
        r.addWidget(QLabel("プレビュー（Cの中身をB直下へ移動）"))
        self.list_preview = QListWidget(); r.addWidget(self.list_preview, 1)
        self.cmb_conflict = QComboBox()
        self.cmb_conflict.addItems(["衝突時：スキップ", "衝突時：上書き", "衝突時：自動リネーム(_1,_2…)"])
        self.btn_preview_clear = QPushButton("プレビューをクリア"); self.btn_preview_clear.clicked.connect(self._clear_preview)
        self.btn_preview = QPushButton("選択からプレビュー生成"); self.btn_preview.clicked.connect(self._make_preview)
        self.btn_run = QPushButton("移動を実行"); self.btn_run.clicked.connect(self._run)
        r2 = QHBoxLayout(); r2.addWidget(self.cmb_conflict); r2.addStretch(); r2.addWidget(self.btn_preview_clear); r2.addWidget(self.btn_preview); r2.addWidget(self.btn_run)
        r.addLayout(r2)

        undo_row = QHBoxLayout()
        self.btn_undo = QPushButton("Undo（直前の実行を取り消し）"); self.btn_undo.clicked.connect(self._undo_last)
        self.btn_redo = QPushButton("Redo（直前のUndoをやり直し）"); self.btn_redo.clicked.connect(self._redo_last)
        undo_row.addWidget(self.btn_undo); undo_row.addWidget(self.btn_redo); undo_row.addStretch()
        r.addLayout(undo_row)

        splitter.addWidget(left_panel); splitter.addWidget(right_panel); splitter.setSizes([440, 560])
        main.addWidget(splitter, 1)

        self.progress = QProgressBar(); self.progress.setValue(0); main.addWidget(self.progress)

        # 内部
        self.A_path = ""
        self.structure = {}
        self.preview_ops = []
        self.undo_stack: List[List[MoveRecord]] = []
        self.redo_stack: List[List[MoveRecord]] = []

        if self._last_A and os.path.isdir(self._last_A):
            QTimer.singleShot(50, lambda: self._load_root(self._last_A))

        bg.installEventFilter(self); self._bg = bg
        self.raise_(); self.activateWindow()
        load_window_state(self, self._config)  # 位置/サイズ復元 

    # ===== ウィンドウ制御 =====
    def _toggle_max(self):
        if self.isMaximized(): self.showNormal()
        else: self.showMaximized()
        self.btn_max.setText("❏" if self.isMaximized() else "🗖")

    def eventFilter(self, obj, e):
        if obj is self._bg:
            if e.type() == QEvent.MouseButtonPress and e.button() == Qt.LeftButton:
                pos = self.mapFromGlobal(e.globalPosition().toPoint())
                edges = self._edge_at(pos)
                if edges:
                    self._resizing = True; self._resize_edges = edges
                    self._start_geo = self.geometry(); self._start_mouse = e.globalPosition().toPoint()
                else:
                    self._moving = True
                    self._drag_offset = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
                return True
            elif e.type() == QEvent.MouseMove:
                if self._resizing:
                    self._resize_to(e.globalPosition().toPoint()); return True
                if self._moving and (e.buttons() & Qt.LeftButton) and not self.isMaximized():
                    self.move(e.globalPosition().toPoint() - self._drag_offset); return True
                self._update_cursor(self._edge_at(self.mapFromGlobal(e.globalPosition().toPoint())))
            elif e.type() == QEvent.MouseButtonRelease:
                self._resizing = False; self._moving = False; return True
        return super().eventFilter(obj, e)

    def _edge_at(self, pos):
        m = RESIZE_MARGIN; r = self._bg.rect(); edges = ""
        if pos.y() <= m: edges += "T"
        if pos.y() >= r.height()-m: edges += "B"
        if pos.x() <= m: edges += "L"
        if pos.x() >= r.width()-m: edges += "R"
        return edges

    def _update_cursor(self, edges):
        if edges in ("TL","BR"): self.setCursor(Qt.SizeFDiagCursor)
        elif edges in ("TR","BL"): self.setCursor(Qt.SizeBDiagCursor)
        elif edges in ("L","R"): self.setCursor(Qt.SizeHorCursor)
        elif edges in ("T","B"): self.setCursor(Qt.SizeVerCursor)
        else: self.setCursor(Qt.ArrowCursor)

    def _resize_to(self, gpos):
        dx = gpos.x() - self._start_mouse.x(); dy = gpos.y() - self._start_mouse.y()
        geo = self._start_geo; x,y,w,h = geo.x(),geo.y(),geo.width(),geo.height()
        minw, minh = self.minimumSize().width(), self.minimumSize().height()
        if "L" in self._resize_edges: new_w = max(minw, w - dx); x += (w - new_w); w = new_w
        if "R" in self._resize_edges: w = max(minw, w + dx)
        if "T" in self._resize_edges: new_h = max(minh, h - dy); y += (h - new_h); h = new_h
        if "B" in self._resize_edges: h = max(minh, h + dy)
        self.setGeometry(x, y, w, h)

    def closeEvent(self, e):
        save_window_state(self, self._config)  # 保存 
        self._config.save()                    # 保存（JSON）
        return super().closeEvent(e)

    # ===== Aの指定 =====
    def _choose_root(self):
        d = QFileDialog.getExistingDirectory(self, "親フォルダ(A)を選択")
        if d: self._load_root(d)
    def _on_root_dropped(self, path): self._load_root(path)

    def _load_root(self, path: str):
        if not os.path.isdir(path):
            QMessageBox.warning(self, "エラー", "有効なフォルダを指定してください。"); return
        self.A_path = os.path.abspath(path)
        self.drop.setText(f"A: {self.A_path}")
        self._config.last_root = self.A_path
        self._rescan()

    # ===== スキャン & ツリー構築 =====
    def _rescan(self):
        if not self.A_path: return
        include_hidden = self.chk_include_hidden.isChecked()
        self.structure = scan_structure(self.A_path, include_hidden=include_hidden)
        self._populate_tree()
        self._clear_preview()

    def _populate_tree(self):
        self.tree.blockSignals(True)
        self.tree.clear()
        for B in sorted(self.structure.keys()):
            b_item = QTreeWidgetItem([os.path.basename(B) or B, B])
            b_item.setFlags(b_item.flags() | Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.tree.addTopLevelItem(b_item)
            for C in sorted(self.structure[B]):
                c_item = QTreeWidgetItem([os.path.basename(C) or C, C])
                c_item.setFlags(c_item.flags() | Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                b_item.addChild(c_item)
        self.tree.expandAll()
        self.tree.blockSignals(False)

    # ===== リネーム（UI→実体へ即時反映） =====
    def _on_tree_item_changed(self, item: QTreeWidgetItem, col: int):
        if col != 0: return
        old_path = item.text(1)
        if not old_path or not os.path.isdir(old_path):
            return
        new_name = item.text(0).strip()
        base_name = os.path.basename(old_path)
        parent_dir = os.path.dirname(old_path)

        if not new_name:
            self._with_tree_block(lambda: item.setText(0, base_name))
            QMessageBox.warning(self, "リネーム", "空白はできません。")
            return

        new_path = os.path.join(parent_dir, new_name)
        if new_path == old_path:
            return
        if os.path.exists(new_path):
            self._with_tree_block(lambda: item.setText(0, base_name))
            QMessageBox.warning(self, "リネーム", "同名のフォルダが既にあります。")
            return

        try:
            os.replace(old_path, new_path)
            shell_notify_rename(old_path, new_path, is_folder=True)
        except Exception as e:
            self._with_tree_block(lambda: item.setText(0, base_name))
            QMessageBox.critical(self, "リネーム失敗", f"{old_path} -> {new_path}\n{e}")
            return

        self._with_tree_block(lambda: item.setText(1, new_path))
        self._update_child_paths(item, old_path, new_path)

        self.undo_stack.append([MoveRecord(src_before=old_path, dst_after=new_path)])
        self.redo_stack.clear()

    def _with_tree_block(self, fn):
        self.tree.blockSignals(True)
        try:
            fn()
        finally:
            self.tree.blockSignals(False)

    def _update_child_paths(self, item: QTreeWidgetItem, old_root: str, new_root: str):
        for i in range(item.childCount()):
            ch = item.child(i)
            p_old = ch.text(1)
            if p_old.startswith(old_root):
                p_new = new_root + p_old[len(old_root):]
                ch.setText(1, p_new)
            self._update_child_paths(ch, old_root, new_root)

    # ===== プレビュー関連 =====
    def _make_preview(self):
        items = self.tree.selectedItems()
        if not items:
            QMessageBox.information(self, "情報", "B配下のCフォルダを選んでね（複数可）")
            return
        Cs: List[str] = []
        for it in items:
            path = it.text(1)
            if it.childCount() > 0:
                for i in range(it.childCount()):
                    Cs.append(it.child(i).text(1))
            else:
                Cs.append(path)
        Cs = sorted(set([p for p in Cs if os.path.isdir(p)]))
        mode = self._conflict_mode()
        self.preview_ops = build_preview(Cs, mode)
        self._fill_preview_list(self.preview_ops)

    def _clear_preview(self):
        self.preview_ops = []
        self.list_preview.clear()
        self.progress.setValue(0)
        self.lbl_title.setText("プレビュー: 0/0 件")

    def _conflict_mode(self) -> ConflictMode:
        idx = self.cmb_conflict.currentIndex()
        return [ConflictMode.SKIP, ConflictMode.OVERWRITE, ConflictMode.RENAME][idx]

    def _fill_preview_list(self, ops):
        self.list_preview.clear()
        total = len(ops)
        moved = sum(1 for o in ops if o.perform)
        for op in ops:
            label = f"{os.path.basename(op.src)}  →  {op.dst}  [{op.status}]"
            item = QListWidgetItem(label)
            if not op.perform:
                item.setForeground(Qt.gray)
            self.list_preview.addItem(item)
        self.progress.setValue(0)
        self.lbl_title.setText(f"プレビュー: {moved}/{total} 件が対象")

    # ===== 実行 & Undo/Redo =====
    def _run(self):
        if not self.preview_ops:
            QMessageBox.information(self, "情報", "プレビューを作ってください")
            return
        simulate = self.chk_simulate.isChecked()
        total = len(self.preview_ops)
        confirm = QMessageBox.question(
            self, "確認",
            f"{total} 件の移動を実行します。\n"
            f"・衝突モード：{self.cmb_conflict.currentText()}\n"
            f"・ドライトラン：{'ON' if simulate else 'OFF'}\n\nよろしい？",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes: return

        def on_progress(done, total):
            self.progress.setValue(int(done / max(1,total) * 100))

        errors, forward_moves = execute_operations(
            self.preview_ops, simulate=simulate, keep_empty_folder=True, progress_cb=on_progress
        )
        if errors:
            QMessageBox.warning(self, "完了（一部エラー）", "一部でエラー:\n" + "\n".join(errors[:30]))
        else:
            QMessageBox.information(self, "完了", "処理が完了しました")

        if not simulate and forward_moves:
            self.undo_stack.append(forward_moves)
            self.redo_stack.clear()

        self._rescan()

    def _undo_last(self):
        if not self.undo_stack:
            QMessageBox.information(self, "Undo", "履歴なし"); return
        forward_moves = self.undo_stack.pop()
        errors: List[str] = []
        redo_moves: List[MoveRecord] = []

        for mv in reversed(forward_moves):
            src_now = mv.dst_after
            dst_back = mv.src_before
            real_dst = self._safe_target(dst_back, suffix="_undo")
            try:
                if os.path.exists(src_now):
                    os.replace(src_now, real_dst)
                    redo_moves.append(MoveRecord(src_before=real_dst, dst_after=mv.dst_after))
            except Exception as e:
                errors.append(f"{src_now} -> {real_dst} : {e}")

        if redo_moves: self.redo_stack.append(redo_moves)
        if errors:
            QMessageBox.warning(self, "Undo（一部エラー）", "一部でエラー:\n" + "\n".join(errors[:30]))
        else:
            QMessageBox.information(self, "Undo", "直前の操作を元に戻しました。")
        self._rescan()

    def _redo_last(self):
        if not self.redo_stack:
            QMessageBox.information(self, "Redo", "履歴なし"); return
        moves = self.redo_stack.pop()
        errors: List[str] = []
        forward_again: List[MoveRecord] = []

        for mv in moves:
            src = mv.src_before
            dst = mv.dst_after
            real_dst = self._safe_target(dst, suffix="_redo")
            try:
                if os.path.exists(src):
                    os.replace(src, real_dst)
                    forward_again.append(MoveRecord(src_before=src, dst_after=real_dst))
            except Exception as e:
                errors.append(f"{src} -> {real_dst} : {e}")

        if forward_again: self.undo_stack.append(forward_again)
        if errors:
            QMessageBox.warning(self, "Redo（一部エラー）", "一部でエラー:\n" + "\n".join(errors[:30]))
        else:
            QMessageBox.information(self, "Redo", "元の状態に復元。")
        self._rescan()

    def _safe_target(self, base_path: str, suffix="_tmp") -> str:
        if not os.path.exists(base_path): return base_path
        root, ext = os.path.splitext(base_path); i = 1
        while True:
            cand = f"{root}{suffix}{i}{ext}"
            if not os.path.exists(cand): return cand
            i += 1

    # ===== README ダイアログ =====
    def _show_readme_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("README - FolderLevelUp ©️2025 KisaragiIchigo")
        dlg.setModal(True)

        root = QWidget()
        root.setObjectName("glassRoot")  
        vroot = QVBoxLayout(root); vroot.setContentsMargins(14,14,14,14); vroot.setSpacing(8)

        title = QLabel("README")
        title.setObjectName("titleLabel")
        vroot.addWidget(title)

        te = QTextEdit()
        te.setReadOnly(True)
        te.setMarkdown(README_TEXT)
        te.setStyleSheet("background: transparent; border: none;")  
        vroot.addWidget(te)

        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(dlg.reject)
        btns.accepted.connect(dlg.accept)
        vroot.addWidget(btns)

        lay = QVBoxLayout(dlg); lay.setContentsMargins(10,10,10,10); lay.addWidget(root)
        dlg.resize(720, 520)
        dlg.exec()
