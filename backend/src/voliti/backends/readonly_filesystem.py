# ABOUTME: 只读 FilesystemBackend，用于挂载 Agent Skills 目录
# ABOUTME: 继承 deepagents FilesystemBackend，拒绝所有写入以保护 skills 目录的真相源一致性

from __future__ import annotations

from deepagents.backends.filesystem import FilesystemBackend
from deepagents.backends.protocol import EditResult, FileUploadResponse, WriteResult

_PERMISSION_DENIED = "permission_denied"


class ReadOnlyFilesystemBackend(FilesystemBackend):
    """只读 FilesystemBackend。

    与 `FilesystemBackend` 共享读取能力（read / ls_info / glob_info / grep_raw /
    download_files 及其 async 变体），但所有写入路径被拒绝并返回 `FileOperationError`
    约定的 `"permission_denied"` 错误码（与 `FileUploadResponse.error` 的 Literal 集合一致）。

    使用场景：
    - Coach Agent 的 Skills 目录（`backend/skills/coach/`）需要对模型暴露
      `read_file` / `ls` / `glob` / `grep` 能力以支持渐进式披露，但绝不允许
      模型通过 `write_file` / `edit_file` 污染 skill 真相源。
    """

    def write(self, file_path: str, content: str) -> WriteResult:
        return WriteResult(error=_PERMISSION_DENIED)

    async def awrite(self, file_path: str, content: str) -> WriteResult:
        return WriteResult(error=_PERMISSION_DENIED)

    def edit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> EditResult:
        return EditResult(error=_PERMISSION_DENIED)

    async def aedit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> EditResult:
        return EditResult(error=_PERMISSION_DENIED)

    def upload_files(
        self, files: list[tuple[str, bytes]]
    ) -> list[FileUploadResponse]:
        return [
            FileUploadResponse(path=path, error=_PERMISSION_DENIED) for path, _ in files
        ]

    async def aupload_files(
        self, files: list[tuple[str, bytes]]
    ) -> list[FileUploadResponse]:
        return [
            FileUploadResponse(path=path, error=_PERMISSION_DENIED) for path, _ in files
        ]
