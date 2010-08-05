MAJOR_VERSION=0
MINOR_VERSION=2
MICRO_VERSION=0
VERSION=$(MAJOR_VERSION).$(MINOR_VERSION).$(MICRO_VERSION)
PYSIDE_VERSION=0.4.0
PACKAGE=pyside-tools
TARBALL=$(PACKAGE)-$(VERSION).tar.bz2
WORK_DIR=$(PACKAGE)-$(VERSION)
DISTRO='unstable'
VERSION_NAME='1maemo1'

all: new_release

new_release: debian_version_new.stamp $(TARBALL) dpkg_control.stamp dpkg_sources.stamp
update_release: debian_version_update.stamp $(TARBALL) dpkg_control.stamp dpkg_sources.stamp

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

dpkg_control.stamp:
	cp -rf debian ./build/$(WORK_DIR)/
	sed 's/@PYSIDE_VERSION/$(PYSIDE_VERSION)/g' ./build/$(WORK_DIR)/debian/control > ./build/$(WORK_DIR)/debian/control.new
	mv ./build/$(WORK_DIR)/debian/control.new ./build/$(WORK_DIR)/debian/control

dpkg_sources.stamp:
	cd ./build/$(WORK_DIR)/ && dpkg-buildpackage -rfakeroot -S -I.git -i.git -k$(GPG_KEY)
	touch dpkg_sources.stamp

clean:
	rm -rf dpkg_sources.stamp debian_version_update.stamp debian_version_new.stamp ./build $(TARBALL)
