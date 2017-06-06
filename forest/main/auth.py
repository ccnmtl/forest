""" access policy implementation """


class RequireUser(object):
    def check(self, checker):
        if not checker.user:
            return False


class DenyAnonymous(object):
    def check(self, checker):
        if checker.user.is_anonymous:
            return False


class AllowSuperUser(object):
    def check(self, checker):
        if checker.user.is_superuser:
            return True


class AllowOpen(object):
    def check(self, checker):
        if checker.stand.access == "open":
            return True


class AllowEditUser(object):
    def check(self, checker):
        if checker._access_in(["admin", "faculty", "ta"]):
            return True


class AllowInEditGroup(object):
    def check(self, checker):
        if checker.in_edit_group():
            return True


class AllowStandUser(object):
    def check(self, checker):
        r = checker.standuser()
        if r.count() > 0:
            return True


class AllowUserGroupCanView(object):
    def check(self, checker):
        if checker.user_group_can_x("view"):
            return True


class AllowAdminUser(object):
    def check(self, checker):
        if checker._access_in(["admin"]):
            return True


class AllowInAdminGroup(object):
    def check(self, checker):
        if checker.user_group_can_x("admin"):
            return True


class AccessChecker(object):
    """ centralize access control policy checks """
    def __init__(self, stand, user):
        self.stand = stand
        self.user = user

    def standuser(self):
        return self.stand.standuser_set.filter(user=self.user)

    def _access_in(self, access_list):
        r = self.standuser()
        if r.count() > 0:
            su = r[0]
            if su.access in access_list:
                return True
        return False

    def check(self, policies):
        """ call each policy implementation in order
        short-circuiting out as soon as any of them
        give us an explicity ALLOW/DENY """
        for p in policies:
            status = p.check(self)
            if status is not None:
                return status
        return False

    def can_edit(self):
        policies = [
            RequireUser(),
            DenyAnonymous(),
            AllowSuperUser(),
            AllowEditUser(),
            AllowInEditGroup(),
        ]
        return self.check(policies)

    def can_view(self):
        policies = [
            AllowOpen(),
            RequireUser(),
            DenyAnonymous(),
            AllowSuperUser(),
            AllowStandUser(),
            AllowUserGroupCanView(),
        ]
        return self.check(policies)

    def can_admin(self):
        policies = [
            RequireUser(),
            DenyAnonymous(),
            AllowSuperUser(),
            AllowAdminUser(),
            AllowInAdminGroup(),
        ]
        return self.check(policies)

    def standgroups(self):
        return self.stand.standgroup_set.all()

    def in_edit_group(self):
        allowed_groups = {g.group.name for g in self.standgroups()
                          if g.access in ["admin", "faculty", "ta"]}
        user_groups = {g.name for g in self.user.groups.all()}
        return len(allowed_groups & user_groups) > 0

    def user_group_can_x(self, permission):
        """check if the user is in a group that has access"""
        allowed_groups = {g.group.name for g in self.standgroups()
                          if permission == "view" or g.access == permission}
        user_groups = {g.name for g in self.user.groups.all()}
        return len(allowed_groups & user_groups) > 0
