#
# $Log$
# Revision 2.2  2004/05/24 14:21:24  victor
# ������� �� SCons
#
# Revision 2.8  2004/05/24 13:39:57  victor
# *** empty log message ***
#
# Revision 1.2  2004/05/24 13:34:00  victor
# ������� �� SCons.
#
# Revision 1.18  2004/05/20 15:33:28  victor
# ������� ����� Make�� � Scons.
#
# Revision 2.3  2004/05/20 10:40:37  victor
# ��������� �� $(SCONS).
#
# Revision 2.5  2003/08/27 14:07:24  victor
# ����� ������ �������� ��������� � ������������.
#

SCONS = $(shell which "scons-2" 2>/dev/null || which "scons")

.PHONY: $(MAKECMDGOALS) all
ifdef MAKECMDGOALS
$(MAKECMDGOALS):
else
all:
endif
	$(SCONS) $(MAKECMDGOALS)
