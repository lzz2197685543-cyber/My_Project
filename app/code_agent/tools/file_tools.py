from langchain_community.agent_toolkits.file_management import FileManagementToolkit
from pathlib import Path

Base_dir=Path(__file__).resolve().parent.parent.parent.parent
file_tools = FileManagementToolkit(root_dir=f'{Base_dir}\\temp').get_tools()