MAJOR_VERSION=0
MINOR_VERSION=4
MICRO_VERSION=0
VERSION=$(MAJOR_VERSION).$(MINOR_VERSION).$(MICRO_VERSION)
LIB_APIEXTRACTOR_VERSION=0.7.0
GENERATORRUNNER_VERSION=0.6.0
SHIBOKEN_VERSION=0.4.0
QT_VERSION=4.6
PACKAGE=pyside
TARBALL=$(PACKAGE)-qt$(QT_VERSION)+$(VERSION).tar.bz2
WORK_DIR=$(PACKAGE)-qt$(QT_VERSION)+$(VERSION)
DISTRO='unstable'
VERSION_NAME='1maemo2'
LIB_INSTALL_FILE=lib$(PACKAGE)$(MAJOR_VERSION).$(MINOR_VERSION).install


all: new_release

new_release: debian_version_new.stamp $(TARBALL) ./build/$(WORK_DIR)/debian/$(LIB_INSTALL_FILE) dpkg_sources.stamp
update_release: debian_version_update.stamp $(TARBALL) ./build/$(WORK_DIR)/debian/$(LIB_INSTALL_FILE) dpkg_sources.stamp

debian_version_update.stamp:
	dch -i
	touch debian_version_update.stamp

debian_version_new.stamp:
	dch --newversion='$(VERSION)-$(VERSION_NAME)' --distribution=$(DISTRO)
	touch debian_version_new.stamp

$(TARBALL):
	wget http://www.pyside.org/files/$(TARBALL)
	mkdir build
	tar jxf $(TARBALL) -C ./build

./build/$(WORK_DIR)/debian/$(LIB_INSTALL_FILE):
	cp -rf debian ./build/$(WORK_DIR)/
	mv ./build/$(WORK_DIR)/debian/lib$(PACKAGE).install ./build/$(WORK_DIR)/debian/$(LIB_INSTALL_FILE)
	sed 's/@VERSION/$(MAJOR_VERSION).$(MINOR_VERSION)/g' ./build/$(WORK_DIR)/debian/control > ./build/$(WORK_DIR)/debian/control.new
	sed 's/@SHIBOKEN_VERSION/$(SHIBOKEN_VERSION)/g' ./build/$(WORK_DIR)/debian/control.new > ./build/$(WORK_DIR)/debian/control.new2
	sed 's/@QT_VERSION/$(QT_VERSION)/g' ./build/$(WORK_DIR)/debian/control.new2 > ./build/$(WORK_DIR)/debian/control.new
	sed 's/@GENERATORRUNNER_VERSION/$(GENERATORRUNNER_VERSION)/g' ./build/$(WORK_DIR)/debian/control.new > ./build/$(WORK_DIR)/debian/control
	rm ./build/$(WORK_DIR)/debian/control.new2
	rm ./build/$(WORK_DIR)/debian/control.new

dpkg_sources.stamp:
	cd ./build/$(WORK_DIR)/ && dpkg-buildpackage -rfakeroot -S -I.git -i.git -k$(GPG_KEY)
	touch dpkg_sources.stamp

clean:
	rm -rf dpkg_sources.stamp debian_version_update.stamp debian_version_new.stamp ./build $(TARBALL)
