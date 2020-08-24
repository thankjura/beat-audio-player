import re

from gi.repository import Gio, GLib


__all__ = ['DBusInterface']


def camelcase_to_snake_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    method_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    if method_name == "raise":
        return "_raise"

    return method_name


class DBusInterface:
    def __init__(self, app_id, xml_resource):
        self.__path = "/org/mpris/MediaPlayer2"
        self.__name = f"org.mpris.MediaPlayer2.{app_id}"
        self.__signals = None
        self.__con = None
        self.__method_inargs = None
        self.__method_outargs = None
        self.__xml_resource = xml_resource
        self.__xml_doc = None


        Gio.bus_get(Gio.BusType.SESSION, None, self.__bus_get_sync, self.__name)

    def __bus_get_sync(self, source, res, name):
        try:
            self.__con = Gio.bus_get_finish(res)
        except GLib.Error as e:
            print(f"Unable to connect to to session bus: {e.message}")
            return

        Gio.bus_own_name_on_connection(
            self.__con, name, Gio.BusNameOwnerFlags.NONE, None, None)

        method_outargs = {}
        method_inargs = {}
        signals = {}

        xml_res = Gio.File.new_for_uri(self.__xml_resource)
        self.__xml_doc = xml_res.load_bytes(None)[0].get_data().decode()

        for interface in Gio.DBusNodeInfo.new_for_xml(self.__xml_doc).interfaces:

            for method in interface.methods:
                method_outargs[method.name] = "(" + "".join(
                    [arg.signature for arg in method.out_args]) + ")"
                method_inargs[method.name] = tuple(
                    arg.signature for arg in method.in_args)

            for signal in interface.signals:
                args = {arg.name: arg.signature for arg in signal.args}
                signals[signal.name] = {
                    'interface': interface.name, 'args': args}

            self.__con.register_object(
                object_path=self.__path, interface_info=interface,
                method_call_closure=self.__on_method_call)

        self.__method_inargs = method_inargs
        self.__method_outargs = method_outargs
        self.__signals = signals

    def __on_method_call(
        self, connection, sender, object_path, interface_name, method_name,
            parameters, invocation):
        """GObject.Closure to handle incoming method calls.

        :param Gio.DBusConnection connection: D-Bus connection
        :param str sender: bus name that invoked the method
        :param srt object_path: object path the method was invoked on
        :param str interface_name: name of the D-Bus interface
        :param str method_name: name of the method that was invoked
        :param GLib.Variant parameters: parameters of the method invocation
        :param Gio.DBusMethodInvocation invocation: invocation
        """
        args = list(parameters.unpack())
        for i, sig in enumerate(self.__method_inargs[method_name]):
            if sig == 'h':
                msg = invocation.get_message()
                fd_list = msg.get_unix_fd_list()
                args[i] = fd_list.get(args[i])

        method_snake_name = camelcase_to_snake_case(method_name)
        try:
            result = getattr(self, method_snake_name)(*args)
        except ValueError as e:
            invocation.return_dbus_error(interface_name, str(e))
            return

        result = (result,)
        out_args = self.__method_outargs[method_name]
        if out_args != '()':
            variant = GLib.Variant(out_args, result)
            invocation.return_value(variant)
        else:
            invocation.return_value(None)

    def dbus_emit_signal(self, signal_name, values):
        if self.__signals is None:
            return

        signal = self.__signals[signal_name]
        parameters = []
        for arg_name, arg_signature in signal['args'].items():
            value = values[arg_name]
            parameters.append(GLib.Variant(arg_signature, value))

        variant = GLib.Variant.new_tuple(*parameters)
        self.__con.emit_signal(
            None, self.__path, signal['interface'], signal_name, variant)

    def introspect(self):
        return self.__xml_doc

    
