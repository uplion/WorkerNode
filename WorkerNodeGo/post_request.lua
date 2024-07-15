wrk.method = "POST"
wrk.body   = '{"model": "static","messages": [{"role": "user","content": "Hello"}]}'
wrk.headers["Content-Type"] = "application/json"
