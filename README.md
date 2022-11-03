# Code Run Service

This is a demo microservice which demonstrates the abilities of 
[RunBox](https://github.com/burenotti/runbox) and my skills in FastAPI.

## What it can?
The microservice allows you to build and run untrusted code in docker container
and interact with it using websockets.


## Try it out
### Set up
You can use docker-compose to run project.

First of all you need to provide .env file in the root of the project:
```dotenv

```
Then build and startup service using docker-compose.
```shell
docker-compose up
```
### Service works! 🎉 
Now you can open http://127.0.0.1:8080/docs and checkout the docs.