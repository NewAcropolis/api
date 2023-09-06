# Quickstart

Please ensure that you have [docker](https://docs.docker.com/desktop/) and [docker-compose](https://docs.docker.com/compose/) installed on your machine before proceeding. 

Then to start creating your docker stack run this command - 

```bash
docker-compose -f docker/docker-compose.yml build
```

Once that has finished building the docker stack you can start it up 

```bash
docker-compose -f docker/docker-compose.yml up
```

This will also run the data setup which will create some dummy data that you can use to run the frontend app against. Update the data in the json as needed to display things correctly in the frontend or update things as needed in the admin area.

You should be able to make calls to the API by running this command -

```bash
curl localhost:5001
```

This will give you the current state of the stack.

To run the tests you can run this command -

```bash
docker exec na_api make test
```

If you want to exec onto the api container in order to update code run this command

```bash
docker exec -it na_api bash
```

## Connecting to the API

Update the frontend app to point to the API using this value - `http://localhost:5001`

## Testing code changes on the stack

Exec onto the `na_api` docker container and use `vi` to modify files on the API, the changes should be automatically picked up. If you want to keep any changes remember to update the changes in the source on your IDE not in the docker container.

## Resetting the stack

If you want to clear down the stack run these commands -

```bash
docker-compose -f docker/docker-compose.yml down
yes y | docker volume prune
```
