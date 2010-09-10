MAJOR_VERSION=0
MINOR_VERSION=8
MICRO_VERSION=0
LIB_SUFFIX=$(MAJOR_VERSION).$(MINOR_VERSION)
VERSION=$(MAJOR_VERSION).$(MINOR_VERSION).$(MICRO_VERSION)
PACKAGE_NAME='apiextractor'
TARBALL=apiextractor-$(VERSION).tar.bz2
WORK_DIR=apiextractor-$(VERSION)
DISTRO='lucid'
VERSION_NAME='ubuntu'

all: new_release


new_release: debian_version_new.stamp $(TARBALL) ./build/$(WORK_DIR)/debian/libapiextract$(MAJOR_VERSION).$(MINOR_VERSION).install dpkg_sources.stamp
update_release: debian_version_update.stamp $(TARBALL) ./build/$(WORK_DIR)/debian/libapiextract$(MAJOR_VERSION).$(MINOR_VERSION).install dpkg_sources.stamp

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

./build/$(WORK_DIR)/debian/libapiextract$(MAJOR_VERSION).$(MINOR_VERSION).install:
	cp -rf debian ./build/$(WORK_DIR)/
	mv ./build/$(WORK_DIR)/debian/libapiextractor.install ./build/$(WORK_DIR)/debian/libapiextractor$(LIB_SUFFIX).install
	mv ./build/$(WORK_DIR)/debian/libapiextractor-dev.install ./build/$(WORK_DIR)/debian/libapiextractor$(LIB_SUFFIX)-dev.install
	mv ./build/$(WORK_DIR)/debian/libapiextractor-dbg.install ./build/$(WORK_DIR)/debian/libapiextractor$(LIB_SUFFIX)-dbg.install
	sed 's/@LIB_SUFFIX/$(MAJOR_VERSION).$(MINOR_VERSION)/g' debian/control > ./build/$(WORK_DIR)/debian/control
	sed 's/@LIB_SUFFIX/$(MAJOR_VERSION).$(MINOR_VERSION)/g' debian/rules > ./build/$(WORK_DIR)/debian/rules

dpkg_sources.stamp:
	cd ./build/$(WORK_DIR)/ && dpkg-buildpackage -rfakeroot -S -I.git -i.git -k$(GPG_KEY)
	touch dpkg_sources.stamp

clean:
	rm -rf dpkg_sources.stamp debian_version_update.stamp debian_version_new.stamp ./build $(TARBALL)
