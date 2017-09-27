#######################################
### Dev targets
#######################################
dev-dep:
	sudo apt-get install python3-virtualenv

dev-pyenv:
	virtualenv -p /usr/bin/python3 env
	env/bin/pip3 install -r requirements.txt --upgrade --force-reinstall
	env/bin/python setup.py develop
	env/bin/pip3 install ipdb pylint pycodestyle


#######################################
### Documentation
#######################################
doc-update-refs:
	rm -rf doc/source/refs/
	sphinx-apidoc -M -f -e -o doc/source/refs/ tuxdroid/

doc-generate:
	cd doc && make html

#######################################
### Test targets
#######################################
test-run: test-syntax test-pytest

test-syntax:
	env/bin/pycodestyle --max-line-length=100 tuxdroid
	env/bin/pylint --rcfile=.pylintrc -r no tuxdroid

test-pytest:
	rm -rf .coverage nosetest.xml nosetests.html htmlcov
	env/bin/pytest --html=pytest/report.html --self-contained-html --junit-xml=pytest/junit.xml --cov=tuxdroid/ --cov-report=term --cov-report=html:pytest/coverage/html --cov-report=xml:pytest/coverage/coverage.xml tests 
	coverage combine || true
	coverage report --include='*/tuxdroid/*'
	# CODECLIMATE_REPO_TOKEN=${CODECLIMATE_REPO_TOKEN} codeclimate-test-reporter
