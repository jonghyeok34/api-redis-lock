
def api_lock(
    param: str = None,  # params for lock -
    http_status: int = 400,
    content: dict = {"message": "잠시후에 시도해주세요."},
    ttl: int = 60,  # ttl(seconds)
):
    def wrapper(func):
        """logging function"""

        @wraps(func)
        async def inner(*args, **kwargs):
            function_repo = LockRedisRepo(redis_client=product_redis_client)
            function_name = func.__name__
            if param:
                # 해당 param에 대한 value 구하기
                param_path = param.split(".")
                param_val = None

                for i in range(len(param_path)):
                    current_param = param_path[i]
                    if i == 0:
                        param_val = kwargs.get(current_param)
                    else:
                        if type(param_val) == dict:
                            param_val = param_val.get(current_param)
                        else:
                            param_val = param_val.__dict__.get(current_param)

                # get param value
                if param_val:
                    try:
                        if function_repo.is_function_locked(
                            function_name=function_name, key=param_val
                        ):
                            raise FunctionLockedException(
                                http_status=http_status, content=content
                            ) from None
                        else:
                            function_repo.set_function_locked(
                                function_name=function_name,
                                key=param_val,
                                locked=True,
                                ttl=ttl,
                            )

                        result = await func(*args, **kwargs)
                    except FunctionLockedException as e:
                        return JSONResponse(
                            status_code=e.http_status,
                            content=e.content,
                        )
                    finally:
                        function_repo.set_function_locked(
                            function_name=function_name,
                            key=param_val,
                            locked=False,
                            ttl=ttl,
                        )
                else:
                    result = await func(*args, **kwargs)
            else:
                result = await func(*args, **kwargs)
            return result

        return inner

    return wrapper
