import torch
import torch.nn as nn
import torch.nn.functional as F

from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

from nsp3.base import ModelBase
from nsp3.utils import setup_logger
from nsp3.embeddings import ESM1bEmbedding

from nsp3.embeddings import decode_to_protein_sequence

log = setup_logger(__name__)


class ESM1b(ModelBase):
    def __init__(self, in_features: int, language_model: str):
        """ Initializes the model
        Args:
            in_features [int]: size of the embedding features
            language_model: path to the language model weights
        """
        super(ESM1b, self).__init__()

        self.embedding = ESM1bEmbedding(language_model)

        # Task block
        self.ss8 = nn.Sequential(*[
            nn.Linear(in_features=in_features, out_features=8),
        ])
        self.ss3 = nn.Sequential(*[
            nn.Linear(in_features=in_features, out_features=3),
        ])
        self.disorder = nn.Sequential(*[
            nn.Linear(in_features=in_features, out_features=2),
        ])
        self.rsa = nn.Sequential(*[
            nn.Linear(in_features=in_features, out_features=1),
            nn.Sigmoid()
        ])
        self.phi = nn.Sequential(*[
            nn.Linear(in_features=in_features, out_features=2),
            nn.Tanh()
        ])
        self.psi = nn.Sequential(*[
            nn.Linear(in_features=in_features, out_features=2),
            nn.Tanh()
        ])

        log.info(f'<init>: \n{self}')

    def forward(self, x, mask):
        padding_length = x.shape[1]
        x = decode_to_protein_sequence(x.cpu().numpy())

        x = self.embedding(x)
        x = F.pad(x, pad=(0, 0, padding_length-x.shape[1], 0), mode='constant', value=0)

        # hidden neurons to classes
        ss8 = self.ss8(x)
        ss3 = self.ss3(x)
        dis = self.disorder(x)
        rsa = self.rsa(x)
        phi = self.phi(x)
        psi = self.psi(x)

        return [ss8, ss3, dis, rsa, phi, psi]
