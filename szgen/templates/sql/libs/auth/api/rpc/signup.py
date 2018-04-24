from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

__all__ = ('signup',)

signup = Template("""\e # Creating signup(email, password) function. Modify this if you want to use a different signup.
create or replace function signup(email text, password text) returns session as $$$$
declare
    usr record;
    result record;
    usr_api record;
begin
    EXECUTE format(
        ' insert into %I."user" as u'
        ' (email, password) values'
        ' ($$1, $$2)'
        ' returning row_to_json(u.*) as j'
        , quote_ident(settings.get('auth.data-schema')))
    INTO usr
    USING $$1, $$2;

    EXECUTE format(
        ' select json_populate_record(null::%I."user", $$1) as r'
        , quote_ident(settings.get('auth.api-schema')))
    INTO usr_api
    USING usr.j;

    result := (
        row_to_json(usr_api.r),
        auth.sign_jwt(auth.get_jwt_payload(usr.j))
    );

    return result;
end
$$$$ security definer language plpgsql;

revoke all privileges on function signup(text, text) from public;
""")
