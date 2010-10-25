MAJOR_VERSION=0
MINOR_VERSION=8
MICRO_VERSION=1
VERSION=$(MAJOR_VERSION).$(MINOR_VERSION).$(MICRO_VERSION)
TARBALL=apiextractor-$(VERSION).tar.bz2
WORK_DIR=apiextractor-$(VERSION)
DISTRO='unstable'
VERSION_NAME='1maemo1'

all: new_release


new_release: debian_version_new.stamp $(TARBALL) ./build/$(WORK_DIR)/debian/libapiextract$(MAJOR_VERSION).$(MINOR_VERSION).install dpkg_sources.stamp
update_release: debian_version_update.stamp $(TARBALL) ./build/$(WORK_DIR)/debian/libapiextract$(MAJOR_VERSION).$(MINOR_VERSION).install dpkg_sources.stamp

debian_version_update.stamp:
	dch -i
	touch debian_version_update.stamp

debian_version_new.stamp:
	dch --newversion='$(VERSION)-$(VERSION_NAME)' --distribution=$(DISTRO)
	touch debian_version_new.stamp

$(TARBALL):
	wget http://www.pyside.org/files/$(TARBALL)
	mkdir build
	tar jxvf $(TARBALL) -C ./build

./build/$(WORK_DIR)/debian/libapiextract$(MAJOR_VERSION).$(MINOR_VERSION).install:
	cp -rf debian ./build/$(WORK_DIR)/
	mv ./build/$(WORK_DIR)/debian/libapiextractor.install ./build/$(WORK_DIR)/debian/libapiextract$(MAJOR_VERSION).$(MINOR_VERSION).install
	sed 's/@VERSION/$(MAJOR_VERSION).$(MINOR_VERSION)/g' debian/control > ./build/$(WORK_DIR)/debian/control

dpkg_sources.stamp:
	cd ./build/$(WORK_DIR)/ && dpkg-buildpackage -rfakeroot -sa -S -I.git -i.git -k$(GPG_KEY)
	touch dpkg_sources.stamp

clean:
	rm -rf dpkg_sources.stamp debian_version_update.stamp debian_version_new.stamp ./build $(TARBALL)
