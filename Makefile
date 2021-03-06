PRODUCT_OWNER := neetjn
PRODUCT_NAME := py-blog
PRODUCT_VERSION := 0.0.0

PRODUCT_IMAGE := ${PRODUCT_OWNER}/${PRODUCT_NAME}:${PRODUCT_VERSION}
PRODUCT_TEST_IMAGE := ${PRODUCT_OWNER}/${PRODUCT_NAME}:test
PRODUCT_MIGRATION_TEST_IMAGE := ${PRODUCT_OWNER}/${PRODUCT_NAME}:migrations-test
MONGODB_IMAGE := mongo:3.6
REDIS_IMAGE := redis
FAKES3_IMAGE := lphoward/fake-s3

build:
	docker build . -t ${PRODUCT_IMAGE}
	docker build . -f tests/Dockerfile -t ${PRODUCT_TEST_IMAGE}
	docker build . -f migrations_tests/Dockerfile -t ${PRODUCT_MIGRATION_TEST_IMAGE}

test:
	@echo "Spinning up mongodb instance"
	docker run --name test-${PRODUCT_NAME}-mongodb -d \
               ${MONGODB_IMAGE}
	@echo "Spinning up redis instance"
	docker run --name test-${PRODUCT_NAME}-redis -d \
							 ${REDIS_IMAGE}
	sleep 5
	@echo "Spinning up fakes3 instance"
	docker run --name test-${PRODUCT_NAME}-fakes3 -d \
							${FAKES3_IMAGE}
	@echo "Spinning up test container"
	docker run --name test-${PRODUCT_NAME}-instance \
               --link test-${PRODUCT_NAME}-mongodb:mongo \
							 --link test-${PRODUCT_NAME}-redis:redis \
							 --link test-${PRODUCT_NAME}-fakes3:fakes3.local \
							 -e BLOG_TEST=TRUE \
               -e BLOG_DB_URI=mongodb://mongo:27017/py-blog \
							 -e BLOG_REDIS_HOST=redis \
							 -e BLOG_FAKE_S3_HOST=fakes3.local:4569 \
               ${PRODUCT_TEST_IMAGE}

test-clean:
	docker rm -f test-${PRODUCT_NAME}-mongodb test-${PRODUCT_NAME}-redis \
							 test-${PRODUCT_NAME}-fakes3 test-${PRODUCT_NAME}-instance || true

test-migrations:
	@echo "Spinning up mongodb instance"
	docker run --name test-${PRODUCT_NAME}-migrations-mongodb -d \
               ${MONGODB_IMAGE}
	sleep 5
	@echo "Spinning up migrations test container"
	docker run --name test-${PRODUCT_NAME}-migrations-instance \
							--link test-${PRODUCT_NAME}-migrations-mongodb:mongo \
							-e BLOG_DB_HOST=mongo \
							${PRODUCT_MIGRATION_TEST_IMAGE}

test-migrations-clean:
	docker rm -f test-${PRODUCT_NAME}-migrations-mongodb test-${PRODUCT_NAME}-migrations-instance || true

publish: build
	docker push ${PRODUCT_IMAGE}
