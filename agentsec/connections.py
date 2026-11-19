"""Connection discovery and tool compatibility checks; never downloads models."""
import json
import os
import urllib.request
from urllib.parse import urlsplit

from .gateway import READ, tool_definitions
from .model_adapter import ModelAdapter, ModelConfig, ModelError


def connection_config(payload):
    base = payload.get('base_url') or os.environ.get('AGENTSEC_MODEL_BASE_URL', 'http://localhost:11434/v1')
    if not isinstance(base, str):
        raise ValueError('Endpoint must be a URL string.')
    parsed = urlsplit(base)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('Use an HTTP(S) endpoint without credentials, query, or fragment.')
    model = payload.get('model') or os.environ.get('AGENTSEC_MODEL', '')
    if not isinstance(model, str) or not model.strip():
        raise ValueError('Select or enter a model identifier.')
    # Only send the environment credential to its configured endpoint.
    configured = os.environ.get('AGENTSEC_MODEL_BASE_URL', 'http://localhost:11434/v1').rstrip('/')
    env = dict(os.environ, AGENTSEC_MODEL=model.strip(), AGENTSEC_MODEL_BASE_URL=base.rstrip('/'))
    if base.rstrip('/') != configured:
        env.pop('AGENTSEC_MODEL_API_KEY', None)
    return ModelConfig.from_env(env=env)


def discover_models(payload):
    cfg = connection_config(dict(payload, model=payload.get('model') or '_discovery'))
    headers = {'Authorization': 'Bearer ' + cfg.api_key} if cfg.api_key else {}
    request = urllib.request.Request(cfg.base_url + '/models', headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            data = json.load(response)
        models = [item['id'] for item in data['data'] if isinstance(item.get('id'), str)]
        return {'status': 'reachable', 'models': models}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return {'status': 'discovery_unavailable', 'models': [],
                'message': 'Model discovery unavailable. Check the endpoint or enter a model manually.'}


def test_connection(payload):
    cfg = connection_config(payload)
    discovery = discover_models(payload)
    if discovery['status'] == 'reachable' and cfg.model not in discovery['models']:
        return {'status': 'missing_model', 'message': 'Model is not listed by this endpoint.'}
    try:
        reply = ModelAdapter(cfg).chat([
            {'role': 'user', 'content': 'Call read_login_evidence with empty arguments now.'}
        ], tool_definitions(), timeout_s=30)
    except ModelError as exc:
        return {'status': exc.kind, 'message': 'Connection test failed: ' + exc.kind}
    compatible = any(call['name'] == READ and call['arguments'] == {} for call in reply['tool_calls'])
    return {'status': 'tool_compatible' if compatible else 'tool_incompatible',
            'message': 'Valid read tool request observed; no tool executed.' if compatible else
                       'Endpoint responded, but no valid read tool request was observed.'}
