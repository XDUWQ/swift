import copy
import os
import shutil
import tempfile
import unittest
from time import time

import torch
from modelscope.models.nlp.structbert import (SbertConfig,
                                              SbertForSequenceClassification)
from peft.utils import WEIGHTS_NAME

from swift import LoraConfig, Swift, push_to_hub


class TestPeft(unittest.TestCase):

    def setUp(self):
        print(('Testing %s.%s' % (type(self).__name__, self._testMethodName)))
        self.tmp_dir = tempfile.TemporaryDirectory().name
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)
        super().tearDown()

    def test_peft_lora_injection(self):
        model = SbertForSequenceClassification(SbertConfig())
        model2 = copy.deepcopy(model)
        lora_config = LoraConfig(target_modules=['query', 'key', 'value'])
        model = Swift.prepare_model(model, lora_config)
        model.save_pretrained(self.tmp_dir)
        with open(os.path.join(self.tmp_dir, 'configuration.json'), 'w') as f:
            f.write('{}')
        self.assertTrue(
            os.path.exists(os.path.join(self.tmp_dir, WEIGHTS_NAME)))

        revision = str(int(time()))
        push_to_hub(
            'damo/test_swift_peft_model',
            output_dir=self.tmp_dir,
            tag=revision)
        model2 = Swift.from_pretrained(
            model2, 'damo/test_swift_peft_model', revision=revision)
        state_dict = model.state_dict()
        state_dict2 = model2.state_dict()
        for key in state_dict:
            self.assertTrue(key in state_dict2)
            self.assertTrue(
                all(
                    torch.isclose(state_dict[key],
                                  state_dict2[key]).flatten().detach().cpu()))
