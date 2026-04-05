from openenv.core.env_server import create_app

from retail_ops_env.models import RetailOpsAction, RetailOpsObservation
from retail_ops_env.server.case_resolution_env import RetailOpsEnvironment

app = create_app(
    RetailOpsEnvironment,
    RetailOpsAction,
    RetailOpsObservation,
    env_name="retail_ops_env",
)
