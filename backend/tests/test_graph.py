# ABOUTME: graph 模块与 LangGraph 配置测试
# ABOUTME: 验证 langgraph.json 配置正确性与 graph.py 结构

import json
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestLangGraphJson:
    """langgraph.json 配置文件测试。"""

    def test_langgraph_json_is_valid(self) -> None:
        """langgraph.json 应为合法 JSON。"""
        config_path = _PROJECT_ROOT / "langgraph.json"
        config = json.loads(config_path.read_text())
        assert isinstance(config, dict)

    def test_langgraph_json_has_graphs_key(self) -> None:
        """langgraph.json 应包含 graphs 配置。"""
        config_path = _PROJECT_ROOT / "langgraph.json"
        config = json.loads(config_path.read_text())
        assert "graphs" in config
        assert "coach" in config["graphs"]

    def test_langgraph_json_graph_path_points_to_file(self) -> None:
        """langgraph.json 中引用的 graph 文件应存在。"""
        config_path = _PROJECT_ROOT / "langgraph.json"
        config = json.loads(config_path.read_text())
        graph_ref = config["graphs"]["coach"]
        file_path, _var_name = graph_ref.rsplit(":", 1)
        assert (_PROJECT_ROOT / file_path).exists()

    def test_langgraph_json_has_dependencies(self) -> None:
        """langgraph.json 应包含 dependencies 配置。"""
        config_path = _PROJECT_ROOT / "langgraph.json"
        config = json.loads(config_path.read_text())
        assert "dependencies" in config
        assert "." in config["dependencies"]

    def test_langgraph_json_graph_var_name_is_graph(self) -> None:
        """langgraph.json 中引用的变量名应为 graph。"""
        config_path = _PROJECT_ROOT / "langgraph.json"
        config = json.loads(config_path.read_text())
        graph_ref = config["graphs"]["coach"]
        _file_path, var_name = graph_ref.rsplit(":", 1)
        assert var_name == "graph"


class TestGraphModuleStructure:
    """graph.py 源码结构测试（不触发模块级执行）。"""

    def test_graph_py_exists(self) -> None:
        """graph.py 文件应存在。"""
        graph_path = _PROJECT_ROOT / "src" / "voliti" / "graph.py"
        assert graph_path.exists()

    def test_graph_py_has_graph_variable(self) -> None:
        """graph.py 应包含模块级 graph 变量赋值。"""
        graph_path = _PROJECT_ROOT / "src" / "voliti" / "graph.py"
        source = graph_path.read_text()
        assert "graph = create_coach_agent()" in source

    def test_graph_py_calls_init(self) -> None:
        """graph.py 应在模块级调用 init()。"""
        graph_path = _PROJECT_ROOT / "src" / "voliti" / "graph.py"
        source = graph_path.read_text()
        assert "init(_PROJECT_ROOT)" in source

    def test_graph_py_imports_bootstrap(self) -> None:
        """graph.py 应导入 bootstrap.init。"""
        graph_path = _PROJECT_ROOT / "src" / "voliti" / "graph.py"
        source = graph_path.read_text()
        assert "from voliti.bootstrap import init" in source
