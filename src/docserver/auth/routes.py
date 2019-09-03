

@app.route('/logout')
async def logout(request:Request, *args):
    if config.auth_enabled and config.logout_url:
        return RedirectResponse(config.logout_url)
    else:
        return RedirectResponse('/login')


@app.route('/login')
async def login(request:Request, *args):
    if config.auth_enabled:
        return auth_backend.login(request)
    else:
        return RedirectResponse('/')


@app.route('/login/callback')
async def login_callback(request: Request, *args):
    if config.auth_enabled:
        return auth_backend.login_callback(request)
    else:
        return RedirectResponse('/')
