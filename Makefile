PWD=$(shell pwd)
PAGE_DIR=$(PWD)/frontend/dist

setup-frontend:
	npm install

frontend/dist/editor.html: 
	cd frontend; npm run build

build-frontend: frontend/dist/editor.html

setup-backend:
	$(MAKE) -C backend cmd-init-env

run-backend:
	PAGE_DIR=$(PAGE_DIR) $(MAKE) -C backend run