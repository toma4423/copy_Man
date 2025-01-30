import subprocess
from typing import Callable


class WindowsCopy:
    def __init__(
        self, progress_callback: Callable = None, error_callback: Callable = None
    ):
        """
        Windows用のファイルコピークラス

        Parameters:
        progress_callback (Callable): 進行状況を報告するためのコールバック関数
        error_callback (Callable): エラー発生時に呼び出されるコールバック関数
        """
        self.progress_callback = progress_callback
        self.error_callback = error_callback

    def _run_robocopy(self, src: str, dest: str) -> int:
        """
        robocopyコマンドを実行してファイルをコピーする

        Parameters:
        src (str): コピー元ディレクトリ
        dest (str): コピー先ディレクトリ

        Returns:
        int: robocopyの終了コード
        """
        command = ["robocopy", src, dest, "/MIR"]
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)

            # robocopyの終了コードをログに出力
            print(f"robocopy 終了コード: {result.returncode}")

            # 終了コード 0 (成功) や 1 (警告) は正常動作として扱う
            if result.returncode == 0:
                return 0  # 完全成功
            elif result.returncode == 1:
                print("警告: コピーが正常に行われたが、robocopyは警告を出しています。")
                return 0  # 警告も成功扱いとする
            return result.returncode
        except subprocess.CalledProcessError as e:
            # 終了コード 1 をエラーとして扱わない
            if e.returncode > 1:  # 重大なエラーのみをエラーとして扱う
                if self.error_callback:
                    self.error_callback(src, 1, 3, e.stderr)
            return e.returncode

    def copy(self, src: str, dest: str, retries: int = 3):
        """
        ファイルまたはディレクトリをコピーする

        Parameters:
        src (str): コピー元のパス
        dest (str): コピー先のパス
        retries (int): コピー失敗時の最大リトライ回数
        """
        attempt = 0
        while attempt < retries:
            attempt += 1
            result_code = self._run_robocopy(src, dest)

            # robocopy の終了コード 0 は成功
            if result_code == 0:
                if self.progress_callback:
                    # 成功を通知
                    self.progress_callback(
                        1, 1, 100, 100
                    )  # 1つのファイルコピーとして報告
                return

            # エラー発生時、再試行を行うかどうかを決定
            if attempt < retries:
                if self.error_callback:
                    self.error_callback(src, attempt, retries, "リトライ中...")
            else:
                if self.error_callback:
                    self.error_callback(src, attempt, retries, "コピーに失敗しました。")

    def set_progress_callback(self, callback: Callable):
        """
        進行状況コールバックを設定する

        Parameters:
        callback (Callable): 進行状況を報告するためのコールバック関数
        """
        self.progress_callback = callback

    def set_error_callback(self, callback: Callable):
        """
        エラー発生時のコールバックを設定する

        Parameters:
        callback (Callable): エラーを報告するためのコールバック関数
        """
        self.error_callback = callback
