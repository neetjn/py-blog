PRODUCT_OWNER := neetjn
PRODUCT_NAME := py-blog
PRODUCT_VERSION := 0.0.0

PRODUCT_IMAGE := ${PRODUCT_OWNER}/${PRODUCT_NAME}:${PRODUCT_VERSION}
PRODUCT_TEST_IMAGE := ${PRODUCT_OWNER}/${PRODUCT_NAME}:test
MONGODB_IMAGE := mongo:3.6

build:
  docker build . -t ${PRODUCT_IMAGE}
  docker build . -f tests/Dockerfile -t ${PRODUCT_TEST_IMAGE}

test:
  @echo Spinning up mongodb instance
  docker run --name test-${PRODUCT_NAME}-mongodb \
             ${MONGODB_IMAGE}
  sleep 5
  docker run --name test-${PRODUCT_NAME}-instance \
             --link test-${PRODUCT_NAME}-mongodb:mongodb \
             -e BLOG_DB_HOST=mongodb://mongo:27017/py-blog
             ${PRODUCT_TEST_IMAGE}

test-clean:
  docker rm -f test-${PRODUCT_NAME}-mongodb test-${PRODUCT_NAME}-instance

publish: build
  docker push ${PRODUCT_IMAGE}