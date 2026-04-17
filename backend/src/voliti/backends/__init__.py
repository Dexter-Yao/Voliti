# ABOUTME: Voliti 自定义 backend 扩展包
# ABOUTME: 承载基于 deepagents backends 的特化实现（只读挂载等）

from voliti.backends.readonly_filesystem import ReadOnlyFilesystemBackend

__all__ = ["ReadOnlyFilesystemBackend"]
