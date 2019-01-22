import octoprint_signalnotifier

import pytest

class TestClass(object):

    # test 1: that basic works
    def test_basic(self):
        op_sn = octoprint_signalnotifier.SignalNotifierPlugin()
        output = op_sn.generate_command('test_path', '+122211199999', 'test message 123', '+9991112222', None)
        assert output.strip() == 'test_path -u +122211199999 send   -m "test message 123" +9991112222'

    # test 2: that group vs single recipient works
    def test_group(self):
        op_sn = octoprint_signalnotifier.SignalNotifierPlugin()
        output = op_sn.generate_command('test_path', '+122211199999', 'test message 123', 'a_group', None)
        assert output.strip() == 'test_path -u +122211199999 send -g a_group  -m "test message 123"'

    # test 3: that attachment works
    def test_attachment(self):
        op_sn = octoprint_signalnotifier.SignalNotifierPlugin()
        output = op_sn.generate_command('test_path', '+122211199999', 'test message 123', '+9991112222', 'file_123.jpg')
        assert output.strip() == 'test_path -u +122211199999 send  -a "file_123.jpg" -m "test message 123" +9991112222'
