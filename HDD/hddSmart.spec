Summary: HTTP сервер для получения результатов проверки hard-диска.
Name: hddSmart
Version: %(ufo_version.py 0)
Release: %(incr.sh Release)ufo
BuildArch: noarch
License: commercial
Group: UFO/Pos
Distribution: UFO for Linux.
Vendor: Expertek
Packager: Victor Sologoubov <victor.sologubov@expertek.ru>
BuildRequires: ufomake
Requires: awk menush python
# pyufomisc pyufopath pcomm
%if "%_vendor" == "Mageia"
Requires: systemd rpm-helper
%else
Requires: SysVinit
%endif


%description
HTTP сервер для получения результатов проверки hard-диска.

%files
%defattr(-,root,root,-)
/etc/cron.daily/hddSmartRun
/usr/local/bin/hddSmartHttp.sh
/usr/local/share/ufo/python/HDD.pyc
/usr/local/share/ufo/python/hddSmartHttp.pyc
/usr/local/share/ufo/python/delete_entry.pyc
%if "%_vendor" == "Mageia"
%{_unitdir}/hddSmartHttp.service
%endif
%doc


%post
%if "%_vendor" == "Mageia"
%_post_service hddSmartHttp
systemctl enable hddSmartHttp || /bin/true
%else
#######################################
# Правим /etc/inittab
#######################################
setinit=/tmp/setinit.awk-$$

cat > $setinit << "EOF"
BEGIN { FS=":"; n3=0}
/^[ \t]*#/ { print ; next; }
($1 == "13") && ($3=="respawn") && ($4 ~ /tty13/) {
  printf "13:2345:respawn:/usr/local/bin/menush -g tty13 /usr/local/bin/hddSmartHttp.sh\n";
  n3++; next;}
{print; next; }
END { 
  if (n3 == 0)
      printf "13:2345:respawn:/usr/local/bin/menush -g tty13 /usr/local/bin/hddSmartHttp.sh\n";
}
EOF

awk -f $setinit /etc/inittab > /etc/inittab.tmp
cp /etc/inittab /etc/inittab.bak
mv /etc/inittab.tmp /etc/inittab
telinit q
rm $setinit
pkill -t tty13,vc/13
%endif

%preun
%if "%_vendor" == "Mageia"
%_preun_service hddSmartHttp
%else
#######################################
# Правим /etc/inittab
#######################################
if [ "$1" == "0" ]
then

setinit=/tmp/setinit.awk-$$

cat > $setinit << "EOF"
BEGIN { FS=":";}
/^[ \t]*#/ { print ; next; }
($1 == "13") && ($3=="respawn") && ($4 ~ /tty13/) && ($4 ~ /hddSmartHttp.sh/) {
  next;}
{print; next; }
EOF
awk -f $setinit /etc/inittab > /etc/inittab.tmp
cp /etc/inittab /etc/inittab.bak
mv /etc/inittab.tmp /etc/inittab
telinit q
rm $setinit
pkill -t tty13,vc/13
fi
%endif

%clean
true
 
%changelog
* Tue Dec 04 2007 victor <Unknown@unknown> 2.26.0
- Обновление всех RPM до новой версии
