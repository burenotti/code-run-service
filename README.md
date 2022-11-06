# Code Run Service

This is a demo microservice which demonstrates the abilities of 
[RunBox](https://github.com/burenotti/runbox) and my skills in FastAPI.

## What it can?
The microservice allows you to build and run untrusted code in docker container
and interact with it using websockets.


## Try it out
### Set up
You can use docker-compose to run project.

First of all you need to clone the project: 
```shell
git clone https://github.com/burenotti/code-run-service
cd code-run-service
```

This repository provides 4 default pipelines
- Go 1.18
- Python 3.10
- Python 3.11
- Node.JS 18

If you want to use them, you need to pull required images:

```shell
docker pull python:3.10-alpine
docker pull python:3.11-alpine
docker pull node:18
docker pull golang:1.18
```

If you don't you can provide custom pipeline directory in .env file:
```dotenv
RUNBOX__CFG_DIR=
```

Then you need to provide .env file in the root of the project:
```dotenv
UVICORN__HOST=0.0.0.0
UVICORN__PORT=8080
```
 
Then build and startup service using docker-compose.
```shell
docker-compose up
```
### Everything works! 🎉 
Now you can open http://127.0.0.1:8080/docs and checkout the swagger docs.

To test websocket endpoints you can use 
[this postman workspace](https://postman.com/runbox/workspace/code-run-service-api).


## About WebSocket messages
Now service supports four types of messages:
- `add_files`
- `execute`
- `terminate`
- `write_stdin`

#### Add Files
Adds list of files to a container.
##### Parameters:
- `files`: list of files
  - `name`: file path
  - `content`: any text content

```json5
{
  "type": "add_files",
  "files": [
    {
      "name": "file_name.json",
      "content": "Any text content"
    },
    // ...
  ]
}
```


#### Execute
Compiles and Runs program. 
##### Parameters
No additional parameters
```json5
{
  "type": "execute"
}
```


#### Write Stdin
Once you've run a program you can write to its stdin.
##### Parameters
- `content`: data, that will be written into stdin
```json5
{
  "type": "write_stdin",
  "content": "ping!\n"
}
```


#### Write Stdin
Once you've run a program you can write to its stdin.
##### Parameters
- `content`: data, that will be written into stdin
```json5
{
  "type": "write_stdin",
  "content": "ping!\n"
}
```
