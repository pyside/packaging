MAJOR_VERSION=0
MINOR_VERSION=6
MICRO_VERSION=1
LIB_SUFFIX='0.6'
VERSION=$(MAJOR_VERSION).$(MINOR_VERSION).$(MICRO_VERSION)
LIB_APIEXTRACTOR_VERSION='0.8.0'
LIB_APIEXTRACTOR_SUFFIX='0.8'
PACKAGE=generatorrunner
TARBALL=$(PACKAGE)-$(VERSION).tar.bz2
WORK_DIR=$(PACKAGE)-$(VERSION)
DISTRO='lucid'
VERSION_NAME='ubuntu'


all: new_release


new_release: debian_version_new.stamp $(TARBALL) ./build/$(WORK_DIR)/debian/libgenrunner$(MAJOR_VERSION).$(MINOR_VERSION).install dpkg_sources.stamp
update_release: debian_version_update.stamp $(TARBALL) ./build/$(WORK_DIR)/debian/libgenrunner$(MAJOR_VERSION).$(MINOR_VERSION).install dpkg_sources.stamp

debian_version_update.stamp:
	dch -i
	touch debian_version_update.stamp

debian_version_new.stamp:
	dch --newversion='$(VERSION)-1$(VERSION_NAME)0' --distribution=$(DISTRO)
	touch debian_version_new.stamp

$(TARBALL):
	wget http://www.pyside.org/files/$(TARBALL)
	mkdir build
	tar jxvf $(TARBALL) -C ./build

./build/$(WORK_DIR)/debian/libgenrunner$(MAJOR_VERSION).$(MINOR_VERSION).install:
	cp -rf debian ./build/$(WORK_DIR)/
	mv ./build/$(WORK_DIR)/debian/libgenrunner.install ./build/$(WORK_DIR)/debian/libgenrunner$(LIB_SUFFIX).install
	mv ./build/$(WORK_DIR)/debian/libgenrunner-dbg.install ./build/$(WORK_DIR)/debian/libgenrunner$(LIB_SUFFIX)-dbg.install
	mv ./build/$(WORK_DIR)/debian/libgenrunner-dev.install ./build/$(WORK_DIR)/debian/libgenrunner$(LIB_SUFFIX)-dev.install
	mv ./build/$(WORK_DIR)/debian/generatorrunner.install ./build/$(WORK_DIR)/debian/generatorrunner$(LIB_SUFFIX).install
	mv ./build/$(WORK_DIR)/debian/docgenerator.install ./build/$(WORK_DIR)/debian/docgenerator$(LIB_SUFFIX).install
	sed 's/@VERSION/$(MAJOR_VERSION).$(MINOR_VERSION)/g' ./debian/rules > ./build/$(WORK_DIR)/debian/rules
	sed 's/@VERSION/$(MAJOR_VERSION).$(MINOR_VERSION)/g' ./build/$(WORK_DIR)/debian/control > ./build/$(WORK_DIR)/debian/control.1
	sed 's/@LIB_APIEXTRACTOR_SUFFIX/$(LIB_APIEXTRACTOR_SUFFIX)/g' ./build/$(WORK_DIR)/debian/control.1 > ./build/$(WORK_DIR)/debian/control.2
	sed 's/@LIB_APIEXTRACTOR_VERSION/$(LIB_APIEXTRACTOR_VERSION)/g' ./build/$(WORK_DIR)/debian/control.2 > ./build/$(WORK_DIR)/debian/control
	rm ./build/$(WORK_DIR)/debian/control.*

dpkg_sources.stamp:
	cd ./build/$(WORK_DIR)/ && dpkg-buildpackage -rfakeroot -S -I.git -i.git -k$(GPG_KEY)
	touch dpkg_sources.stamp

clean:
	rm -rf dpkg_sources.stamp debian_version_update.stamp debian_version_new.stamp ./build $(TARBALL)
