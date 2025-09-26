import os
import shutil
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Callable, Tuple
from utils import shell_notify_update 

def is_hidden(path: str) -> bool:
    name = os.path.basename(path)
    if not name: return False
    return name.startswith(".")  

def scan_structure(A: str, include_hidden: bool=False) -> Dict[str, List[str]]:
    """
    A配下の直下フォルダをBとして列挙し、各B直下のフォルダをCとして列挙
    戻り値: { B_path: [C_path, ...], ... }
    """
    result: Dict[str, List[str]] = {}
    if not os.path.isdir(A): return result
    for b in os.listdir(A):
        B = os.path.join(A, b)
        if not os.path.isdir(B): continue
        if not include_hidden and is_hidden(B): continue
        Cs: List[str] = []
        for c in os.listdir(B):
            C = os.path.join(B, c)
            if not os.path.isdir(C): continue
            if not include_hidden and is_hidden(C): continue
            Cs.append(C)
        result[B] = Cs
    return result

class ConflictMode(Enum):
    SKIP = 0
    OVERWRITE = 1
    RENAME = 2

@dataclass
class Operation:
    src: str      # C内の"中身"（アイテム）の絶対パス（実行前）
    dst: str      # B直下に置くべき行き先パス
    status: str   # "OK" / "SKIP(衝突)" / "RENAME→xxx" / "OVERWRITE"
    perform: bool 

@dataclass
class MoveRecord:
    src_before: str   # 実行前の元パス
    dst_after: str    # 実行後の先パス

def _decide_dst(dst_base: str, mode: ConflictMode) -> Tuple[str, str, bool]:
    """
    競合解決：dst_base が既に存在する場合の対処
    戻り値: (決定したdst, status, perform)
    """
    if not os.path.exists(dst_base):
        return dst_base, "OK", True
    if mode == ConflictMode.SKIP:
        return dst_base, "SKIP(衝突)", False
    if mode == ConflictMode.OVERWRITE:
        return dst_base, "OVERWRITE", True
    # RENAME: foo -> foo_1, foo_2...
    stem, ext = os.path.splitext(dst_base)
    i = 1
    while True:
        cand = f"{stem}_{i}{ext}"
        if not os.path.exists(cand):
            return cand, f"RENAME→{os.path.basename(cand)}", True
        i += 1

def _iter_items_in_C(C: str) -> List[str]:
    # Cの中の直下アイテム（ファイル/フォルダ両方）を対象
    try:
        return [os.path.join(C, x) for x in os.listdir(C)]
    except Exception:
        return []

def build_preview(C_list: List[str], mode: ConflictMode) -> List[Operation]:
    """
    C群の中身をB直下へあげるプレビューを作成（Cフォルダ自体は残す）
    """
    ops: List[Operation] = []
    for C in C_list:
        if not os.path.isdir(C): continue
        B = os.path.dirname(C)
        for item in _iter_items_in_C(C):
            base = os.path.basename(item)
            dst_base = os.path.join(B, base)
            dst, status, perform = _decide_dst(dst_base, mode)
            ops.append(Operation(src=item, dst=dst, status=status, perform=perform))
    return ops

def _remove_if_exists(path: str):
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    elif os.path.isfile(path):
        try: os.remove(path)
        except Exception: pass

def execute_operations(
    ops: List[Operation],
    simulate: bool=False,
    keep_empty_folder: bool=True,
    progress_cb: Callable[[int,int],None]=None
) -> Tuple[List[str], List[MoveRecord]]:
    """
    プレビューに従って実行。Cフォルダは残す（keep_empty_folder=True）。
    戻り値: (errors, forward_moves)
    """
    errors: List[str] = []
    forward_moves: List[MoveRecord] = []
    total = len(ops)
    done = 0
    for op in ops:
        if progress_cb: progress_cb(done, total)
        done += 1

        if not op.perform:
            continue

        try:
            if os.path.exists(op.dst) and op.status == "OVERWRITE":
                if not simulate:
                    _remove_if_exists(op.dst)

            if not simulate:
                shutil.move(op.src, op.dst)
                forward_moves.append(MoveRecord(src_before=op.src, dst_after=op.dst))
                # ★ Explorerへ更新通知（対象と親ディレクトリ）
                shell_notify_update(op.dst)
                shell_notify_update(os.path.dirname(op.dst), is_dir=True)
        except Exception as e:
            errors.append(f"{op.src} -> {op.dst} : {e}")

    if progress_cb: progress_cb(total, total)
    return errors, forward_moves
