MAJOR_VERSION=0
MINOR_VERSION=1
MICRO_VERSION=0
VERSION=$(MAJOR_VERSION).$(MINOR_VERSION).$(MICRO_VERSION)
QT_VERSION=4.6
PYSIDE_VERSION=0.4.0
LIBMEEGOTOUCH_VERSION=0.20.34.2
PACKAGE=python-meegotouch
#DOWNLOAD_URL=http://www.pyside.org/files
DOWNLOAD_URL=127.0.0.1/luck/
TARBALL=$(PACKAGE)-$(VERSION).tar.bz2
WORK_DIR=$(PACKAGE)-$(VERSION)
DISTRO='unstable'
VERSION_NAME='1maemo1'
INSTALL_FILE=$(PACKAGE)$(MAJOR_VERSION).$(MINOR_VERSION).install

all: new_release

new_release: debian_version_new.stamp $(TARBALL) ./build/$(WORK_DIR)/debian/$(INSTALL_FILE) dpkg_sources.stamp
update_release: debian_version_update.stamp $(TARBALL) ./build/$(WORK_DIR)/debian/$(INSTALL_FILE) dpkg_sources.stamp

debian_version_update.stamp:
	dch -i
	touch debian_version_update.stamp

debian_version_new.stamp:
	dch --newversion='$(VERSION)-$(VERSION_NAME)' --distribution=$(DISTRO)
	touch debian_version_new.stamp

$(TARBALL):
	wget $(DOWNLOAD_URL)/$(TARBALL)
	mkdir build
	tar jxf $(TARBALL) -C ./build

./build/$(WORK_DIR)/debian/$(INSTALL_FILE):
	cp -rf debian ./build/$(WORK_DIR)/
	mv ./build/$(WORK_DIR)/debian/$(PACKAGE).install ./build/$(WORK_DIR)/debian/$(INSTALL_FILE)
	sed 's/@VERSION/$(MAJOR_VERSION).$(MINOR_VERSION)/g' ./build/$(WORK_DIR)/debian/control > ./build/$(WORK_DIR)/debian/control.new
	sed 's/@PYSIDE_VERSION/$(PYSIDE_VERSION)/g' ./build/$(WORK_DIR)/debian/control.new > ./build/$(WORK_DIR)/debian/control.new1
	sed 's/@LIBMEEGOTOUCH_VERSION/$(LIBMEEGOTOUCH_VERSION)/g' ./build/$(WORK_DIR)/debian/control.new1 > ./build/$(WORK_DIR)/debian/control.new2
	sed 's/@QT_VERSION/$(QT_VERSION)/g' ./build/$(WORK_DIR)/debian/control.new2 > ./build/$(WORK_DIR)/debian/control.new
	sed 's/@GENERATORRUNNER_VERSION/$(GENERATORRUNNER_VERSION)/g' ./build/$(WORK_DIR)/debian/control.new > ./build/$(WORK_DIR)/debian/control
	rm ./build/$(WORK_DIR)/debian/control.new2
	rm ./build/$(WORK_DIR)/debian/control.new1
	rm ./build/$(WORK_DIR)/debian/control.new

dpkg_sources.stamp:
	cd ./build/$(WORK_DIR)/ && dpkg-buildpackage -rfakeroot -S -I.git -i.git -k$(GPG_KEY)
	touch dpkg_sources.stamp

clean:
	rm -rf dpkg_sources.stamp debian_version_update.stamp debian_version_new.stamp ./build $(TARBALL)
