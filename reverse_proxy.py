from pyngrok import ngrok
from pyngrok.conf import PyngrokConfig

pyngrok_config = PyngrokConfig(auth_token="1hssImxw1hr36FoOzFmxuvC5VSu_3mqFmYhbjjfyqi5pCB4NV")
ngrok.connect(8080, pyngrok_config=pyngrok_config)
# ngrok.set_auth_token("1hssImxw1hr36FoOzFmxuvC5VSu_3mqFmYhbjjfyqi5pCB4NV")
tunnels = ngrok.get_tunnels()
public_url = tunnels[0].public_url
print(public_url)
