# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This module contains the data classes for the price estimation ABCI application."""
import struct
from abc import ABC
from collections import Counter
from operator import itemgetter
from types import MappingProxyType
from typing import Any
from typing import Counter as CounterType
from typing import Dict, FrozenSet, List, Mapping, Optional, Set, Tuple, Type, cast

from aea.exceptions import enforce

from packages.valory.skills.abstract_round_abci.base import (
    AbstractRound,
    BasePeriodState,
)
from packages.valory.skills.price_estimation_abci.payloads import (
    DeploySafePayload,
    EstimatePayload,
    FinalizationTxPayload,
    ObservationPayload,
    RandomnessPayload,
    RegistrationPayload,
    SelectKeeperPayload,
    SignaturePayload,
    TransactionHashPayload,
    ValidatePayload,
)
from packages.valory.skills.price_estimation_abci.tools import aggregate


def encode_float(value: float) -> bytes:
    """Encode a float value."""
    return struct.pack("d", value)


def rotate_list(my_list: list, positions: int) -> List[str]:
    """Rotate a list n positions."""
    return my_list[positions:] + my_list[:positions]


class PeriodState(BasePeriodState):  # pylint: disable=too-many-instance-attributes
    """
    Class to represent a period state.

    This state is replicated by the tendermint application.
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        participants: Optional[FrozenSet[str]] = None,
        participant_to_randomness: Optional[Mapping[str, RandomnessPayload]] = None,
        most_voted_randomness: Optional[str] = None,
        participant_to_selection: Optional[Mapping[str, SelectKeeperPayload]] = None,
        most_voted_keeper_address: Optional[str] = None,
        safe_contract_address: Optional[str] = None,
        participant_to_votes: Optional[Mapping[str, ValidatePayload]] = None,
        participant_to_observations: Optional[Mapping[str, ObservationPayload]] = None,
        participant_to_estimate: Optional[Mapping[str, EstimatePayload]] = None,
        estimate: Optional[float] = None,
        most_voted_estimate: Optional[float] = None,
        participant_to_tx_hash: Optional[Mapping[str, TransactionHashPayload]] = None,
        most_voted_tx_hash: Optional[str] = None,
        participant_to_signature: Optional[Mapping[str, str]] = None,
        final_tx_hash: Optional[str] = None,
    ) -> None:
        """Initialize a period state."""
        super().__init__(participants=participants)
        self._participant_to_randomness = participant_to_randomness
        self._most_voted_randomness = most_voted_randomness
        self._most_voted_keeper_address = most_voted_keeper_address
        self._safe_contract_address = safe_contract_address
        self._participant_to_selection = participant_to_selection
        self._participant_to_votes = participant_to_votes
        self._participant_to_observations = participant_to_observations
        self._participant_to_estimate = participant_to_estimate
        self._most_voted_estimate = most_voted_estimate
        self._estimate = estimate
        self._participant_to_tx_hash = participant_to_tx_hash
        self._most_voted_tx_hash = most_voted_tx_hash
        self._participant_to_signature = participant_to_signature
        self._final_tx_hash = final_tx_hash

    @property
    def keeper_randomness(self) -> float:
        """Get the keeper's random number [0-1]."""
        res = int(self.most_voted_randomness, base=16) // 10 ** 0 % 10
        return cast(float, res / 10)

    @property
    def participant_to_randomness(self) -> Mapping[str, RandomnessPayload]:
        """Get the participant_to_randomness."""
        enforce(
            self._participant_to_randomness is not None,
            "'participant_to_randomness' field is None",
        )
        return cast(Mapping[str, RandomnessPayload], self._participant_to_randomness)

    @property
    def most_voted_randomness(self) -> str:
        """Get the most_voted_randomness."""
        enforce(
            self._most_voted_randomness is not None,
            "'most_voted_randomness' field is None",
        )
        return cast(str, self._most_voted_randomness)

    @property
    def most_voted_keeper_address(self) -> str:
        """Get the most_voted_keeper_address."""
        enforce(
            self._most_voted_keeper_address is not None,
            "'most_voted_keeper_address' field is None",
        )
        return cast(str, self._most_voted_keeper_address)

    @property
    def safe_contract_address(self) -> str:
        """Get the safe contract address."""
        enforce(
            self._safe_contract_address is not None,
            "'safe_contract_address' field is None",
        )
        return cast(str, self._safe_contract_address)

    @property
    def participant_to_selection(self) -> Mapping[str, SelectKeeperPayload]:
        """Get the participant_to_selection."""
        enforce(
            self._participant_to_selection is not None,
            "'participant_to_selection' field is None",
        )
        return cast(Mapping[str, SelectKeeperPayload], self._participant_to_selection)

    @property
    def participant_to_votes(self) -> Mapping[str, ValidatePayload]:
        """Get the participant_to_votes."""
        enforce(
            self._participant_to_votes is not None,
            "'participant_to_votes' field is None",
        )
        return cast(Mapping[str, ValidatePayload], self._participant_to_votes)

    @property
    def participant_to_observations(self) -> Mapping[str, ObservationPayload]:
        """Get the participant_to_observations."""
        enforce(
            self._participant_to_observations is not None,
            "'participant_to_observations' field is None",
        )
        return cast(Mapping[str, ObservationPayload], self._participant_to_observations)

    @property
    def participant_to_estimate(self) -> Mapping[str, EstimatePayload]:
        """Get the participant_to_estimate."""
        enforce(
            self._participant_to_estimate is not None,
            "'participant_to_estimate' field is None",
        )
        return cast(Mapping[str, EstimatePayload], self._participant_to_estimate)

    @property
    def participant_to_signature(self) -> Mapping[str, str]:
        """Get the participant_to_signature."""
        enforce(
            self._participant_to_signature is not None,
            "'participant_to_signature' field is None",
        )
        return cast(Mapping[str, str], self._participant_to_signature)

    @property
    def final_tx_hash(self) -> str:
        """Get the final_tx_hash."""
        enforce(
            self._final_tx_hash is not None,
            "'final_tx_hash' field is None",
        )
        return cast(str, self._final_tx_hash)

    @property
    def estimate(self) -> float:
        """Get the estimate."""
        enforce(self._estimate is not None, "'estimate' field is None")
        return cast(float, self._estimate)

    @property
    def most_voted_estimate(self) -> float:
        """Get the most_voted_estimate."""
        enforce(
            self._most_voted_estimate is not None, "'most_voted_estimate' field is None"
        )
        return cast(float, self._most_voted_estimate)

    @property
    def encoded_most_voted_estimate(self) -> bytes:
        """Get the encoded (most voted) estimate."""
        return encode_float(self.most_voted_estimate)

    @property
    def most_voted_tx_hash(self) -> str:
        """Get the most_voted_tx_hash."""
        enforce(
            self._most_voted_tx_hash is not None, "'most_voted_tx_hash' field is None"
        )
        return cast(str, self._most_voted_tx_hash)


class PriceEstimationAbstractRound(AbstractRound, ABC):
    """Abstract round for the price estimation skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, self._state)


class RegistrationRound(PriceEstimationAbstractRound):
    """
    This class represents the registration round.

    Input: None
    Output: a period state with the set of participants.

    It schedules the SelectKeeperARound.
    """

    round_id = "registration"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the registration round."""
        super().__init__(*args, **kwargs)

        # a collection of addresses
        self.participants: Set[str] = set()

    def registration(self, payload: RegistrationPayload) -> None:
        """Handle a registration payload."""
        sender = payload.sender

        # we don't care if it was already there
        self.participants.add(sender)

    def check_registration(  # pylint: disable=no-self-use
        self, _payload: RegistrationPayload
    ) -> bool:
        """
        Check a registration payload can be applied to the current state.

        A registration can happen only when we are in the registration state.

        :param: _payload: the payload.
        :return: True.
        """
        return True

    @property
    def registration_threshold_reached(self) -> bool:
        """Check that the registration threshold has been reached."""
        return len(self.participants) == self._consensus_params.max_participants

    def end_block(self) -> Optional[Tuple[BasePeriodState, AbstractRound]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.registration_threshold_reached:
            state = PeriodState(participants=frozenset(self.participants))
            next_round = RandomnessRound(state, self._consensus_params)
            return state, next_round
        return None


class RandomnessRound(PriceEstimationAbstractRound, ABC):
    """
    This class represents the randomness round.

    Input: a set of participants (addresses)
    Output: a set of participants (addresses) and randomness

    It schedules the SelectKeeperARound.
    """

    round_id = "randomness"

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the 'select-keeper' round."""
        super().__init__(*args, **kwargs)
        self.participant_to_randomness: Dict[str, RandomnessPayload] = {}

    def randomness(self, payload: RandomnessPayload) -> None:
        """Handle a 'randomness' payload."""
        sender = payload.sender
        if sender not in self.period_state.participants:
            # sender not in the set of participants.
            return

        if sender in self.participant_to_randomness:
            # sender has already sent its randomness
            return

        self.participant_to_randomness[sender] = payload

    def check_randomness(self, payload: SelectKeeperPayload) -> bool:
        """
        Check an randomness payload can be applied to the current state.

        An randomness transaction can be applied only if:
        - the round is in the 'randomness' state;
        - the sender belongs to the set of participants
        - the sender has not sent its selection yet

        :param: payload: the payload.
        :return: True if the selection is allowed, False otherwise.
        """
        sender_in_participant_set = payload.sender in self.period_state.participants
        sender_has_not_sent_randomness_yet = (
            payload.sender not in self.participant_to_randomness
        )
        return sender_in_participant_set and sender_has_not_sent_randomness_yet

    @property
    def threshold_reached(self) -> bool:
        """Check that the threshold has been reached."""
        counter: CounterType = Counter()
        counter.update(
            payload.randomness for payload in self.participant_to_randomness.values()
        )
        # check that a single selection has at least the consensus # of votes
        consensus_n = self._consensus_params.consensus_threshold
        return any(count >= consensus_n for count in counter.values())

    @property
    def most_voted_randomness(self) -> float:
        """Get the most voted randomness."""
        counter = Counter()  # type: ignore
        counter.update(
            payload.randomness for payload in self.participant_to_randomness.values()
        )
        most_voted_randomness, max_votes = max(counter.items(), key=itemgetter(1))
        if max_votes < self._consensus_params.consensus_threshold:
            raise ValueError("keeper has not enough votes")
        return most_voted_randomness

    def end_block(self) -> Optional[Tuple[BasePeriodState, AbstractRound]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                participant_to_randomness=MappingProxyType(
                    self.participant_to_randomness
                ),
                most_voted_randomness=self.most_voted_randomness,
            )
            next_round = SelectKeeperARound(state, self._consensus_params)
            return state, next_round
        return None


class SelectKeeperRound(PriceEstimationAbstractRound, ABC):
    """
    This class represents the select keeper round.

    Input: a set of participants (addresses)
    Output: the selected keeper.

    It schedules the next_round_class.
    """

    next_round_class: Type[PriceEstimationAbstractRound]

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the 'select-keeper' round."""
        super().__init__(*args, **kwargs)
        self.participant_to_selection: Dict[str, SelectKeeperPayload] = {}

    def select_keeper(self, payload: SelectKeeperPayload) -> None:
        """Handle a 'select_keeper' payload."""
        sender = payload.sender
        if sender not in self.period_state.participants:
            # sender not in the set of participants.
            return

        if sender in self.participant_to_selection:
            # sender has already sent its estimate
            return

        self.participant_to_selection[sender] = payload

    def check_select_keeper(self, payload: SelectKeeperPayload) -> bool:
        """
        Check an select_keeper payload can be applied to the current state.

        An select_keeper transaction can be applied only if:
        - the round is in the 'select_keeper' state;
        - the sender belongs to the set of participants
        - the sender has not sent its selection yet

        :param: payload: the payload.
        :return: True if the selection is allowed, False otherwise.
        """
        sender_in_participant_set = payload.sender in self.period_state.participants
        sender_has_not_sent_selection_yet = (
            payload.sender not in self.participant_to_selection
        )
        return sender_in_participant_set and sender_has_not_sent_selection_yet

    @property
    def selection_threshold_reached(self) -> bool:
        """Check that the selection threshold has been reached."""
        selections_counter: CounterType = Counter()
        selections_counter.update(
            payload.keeper for payload in self.participant_to_selection.values()
        )
        # check that a single selection has at least the consensus # of votes
        consensus_n = self._consensus_params.consensus_threshold
        return any(count >= consensus_n for count in selections_counter.values())

    @property
    def most_voted_keeper_address(self) -> float:
        """Get the most voted keeper."""
        keepers_counter = Counter()  # type: ignore
        keepers_counter.update(
            payload.keeper for payload in self.participant_to_selection.values()
        )
        most_voted_keeper_address, max_votes = max(
            keepers_counter.items(), key=itemgetter(1)
        )
        if max_votes < self._consensus_params.consensus_threshold:
            raise ValueError("keeper has not enough votes")
        return most_voted_keeper_address

    def end_block(self) -> Optional[Tuple[BasePeriodState, AbstractRound]]:
        """Process the end of the block."""
        if self.selection_threshold_reached:
            state = self.period_state.update(
                participant_to_selection=MappingProxyType(
                    self.participant_to_selection
                ),
                most_voted_keeper_address=self.most_voted_keeper_address,
            )
            next_round = self.next_round_class(state, self._consensus_params)
            return state, next_round
        return None


class DeploySafeRound(PriceEstimationAbstractRound):
    """
    This class represents the deploy Safe round.

    Input: a set of participants (addresses) and a keeper
    Output: a period state with the set of participants, the keeper and the Safe contract address.

    It schedules the ValidateSafeRound.
    """

    round_id = "deploy_safe"

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the 'collect-observation' round."""
        super().__init__(*args, **kwargs)
        self._contract_address: Optional[str] = None

    def deploy_safe(self, payload: DeploySafePayload) -> None:
        """Handle a deploy safe payload."""
        sender = payload.sender

        if sender not in self.period_state.participants:
            # sender not in the set of participants.
            return

        if sender != self.period_state.most_voted_keeper_address:
            # the sender is not the elected sender
            return

        if self._contract_address is not None:
            # contract address already set
            return

        self._contract_address = payload.safe_contract_address

    def check_deploy_safe(self, payload: DeploySafePayload) -> bool:
        """
        Check a deploy safe payload can be applied to the current state.

        A deploy safe transaction can be applied only if:
        - the sender belongs to the set of participants
        - the sender is the elected sender
        - the sender has not already sent the contract address

        :param: payload: the payload.
        :return: True if the observation tx is allowed, False otherwise.
        """
        sender_in_participant_set = payload.sender in self.period_state.participants
        sender_is_elected_sender = (
            payload.sender == self.period_state.most_voted_keeper_address
        )
        contract_address_not_set_yet = self._contract_address is None
        return (
            sender_in_participant_set
            and sender_is_elected_sender
            and contract_address_not_set_yet
        )

    @property
    def is_contract_set(self) -> bool:
        """Check that the contract has been set."""
        return self._contract_address is not None

    def end_block(self) -> Optional[Tuple[BasePeriodState, AbstractRound]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.is_contract_set:
            state = self.period_state.update(
                safe_contract_address=self._contract_address
            )
            next_round = ValidateSafeRound(state, self._consensus_params)
            return state, next_round
        return None


class ValidateRound(PriceEstimationAbstractRound):
    """
    This class represents the validate round.

    Input: a period state with the set of participants, the keeper and the Safe contract address.
    Output: a period state with the set of participants, the keeper, the Safe contract address and a validation of the Safe contract address.

    It schedules the positive_next_round_class or negative_next_round_class.
    """

    positive_next_round_class: Type[PriceEstimationAbstractRound]
    negative_next_round_class: Type[PriceEstimationAbstractRound]

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the 'collect-observation' round."""
        super().__init__(*args, **kwargs)
        self.participant_to_votes: Dict[str, ValidatePayload] = {}

    def validate(self, payload: ValidatePayload) -> None:
        """Handle a validate safe payload."""
        sender = payload.sender

        if sender not in self.period_state.participants:
            # sender not in the set of participants.
            return

        if sender in self.participant_to_votes:
            # sender has already sent its vote
            return

        self.participant_to_votes[sender] = payload

    def check_validate(self, payload: ValidatePayload) -> bool:
        """
        Check a validate payload can be applied to the current state.

        A validate transaction can be applied only if:
        - the sender belongs to the set of participants
        - the sender has not already submitted the transaction

        :param: payload: the payload.
        :return: True if the observation tx is allowed, False otherwise.
        """
        sender_in_participant_set = payload.sender in self.period_state.participants
        sender_has_not_sent_vote_yet = payload.sender not in self.participant_to_votes
        return sender_in_participant_set and sender_has_not_sent_vote_yet

    @property
    def positive_vote_threshold_reached(self) -> bool:
        """Check that the vote threshold has been reached."""
        true_votes = sum(
            [payload.vote for payload in self.participant_to_votes.values()]
        )
        # check that "true" has at least the consensus # of votes
        consensus_threshold = self._consensus_params.consensus_threshold
        return true_votes >= consensus_threshold

    @property
    def negative_vote_threshold_reached(self) -> bool:
        """Check that the vote threshold has been reached."""
        false_votes = len(self.participant_to_votes) - sum(
            [payload.vote for payload in self.participant_to_votes.values()]
        )
        # check that "false" has at least the consensus # of votes
        consensus_threshold = self._consensus_params.consensus_threshold
        return false_votes >= consensus_threshold

    def end_block(self) -> Optional[Tuple[BasePeriodState, AbstractRound]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.positive_vote_threshold_reached:
            state = self.period_state.update(
                participant_to_votes=MappingProxyType(self.participant_to_votes)
            )
            next_round = self.positive_next_round_class(state, self._consensus_params)
            return state, next_round
        if self.negative_vote_threshold_reached:
            state = self.period_state.update()
            next_round_ = self.negative_next_round_class(state, self._consensus_params)
            return state, next_round_
        return None


class CollectObservationRound(PriceEstimationAbstractRound):
    """
    This class represents the 'collect-observation' round.

    Input: a period state with the prior round data
    Ouptut: a new period state with the prior round data and the observations

    It schedules the EstimateConsensusRound.
    """

    round_id = "collect_observation"

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the 'collect-observation' round."""
        super().__init__(*args, **kwargs)
        self.participant_to_observations: Dict[str, ObservationPayload] = {}

    def observation(self, payload: ObservationPayload) -> None:
        """Handle an 'observation' payload."""
        sender = payload.sender
        if sender not in self.period_state.participants:
            # sender not in the set of participants.
            return

        if sender in self.participant_to_observations:
            # sender has already sent its observation
            return

        self.participant_to_observations[sender] = payload

    def check_observation(self, payload: ObservationPayload) -> bool:
        """
        Check an observation payload can be applied to the current state.

        An observation transaction can be applied only if:
        - the sender belongs to the set of participants
        - the sender has not already sent its observation

        :param: payload: the payload.
        :return: True if the observation tx is allowed, False otherwise.
        """
        sender_in_participant_set = payload.sender in self.period_state.participants
        sender_has_not_sent_observation_yet = (
            payload.sender not in self.participant_to_observations
        )
        return sender_in_participant_set and sender_has_not_sent_observation_yet

    @property
    def observation_threshold_reached(self) -> bool:
        """Check that the observation threshold has been reached."""
        return (
            len(self.participant_to_observations)
            >= self._consensus_params.consensus_threshold
        )

    def end_block(self) -> Optional[Tuple[BasePeriodState, AbstractRound]]:
        """Process the end of the block."""
        # if reached observation threshold, set the result
        if self.observation_threshold_reached:
            observations = [
                payload.observation
                for payload in self.participant_to_observations.values()
            ]
            estimate = aggregate(*observations)
            state = self.period_state.update(
                participant_to_observations=MappingProxyType(
                    self.participant_to_observations
                ),
                estimate=estimate,
            )
            next_round = EstimateConsensusRound(state, self._consensus_params)
            return state, next_round
        return None


class EstimateConsensusRound(PriceEstimationAbstractRound):
    """
    This class represents the 'estimate_consensus' round.

    Input: a period state with the prior round data
    Ouptut: a new period state with the prior round data and the votes for each estimate

    It schedules the TxHashRound.
    """

    round_id = "estimate_consensus"

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the 'estimate consensus' round."""
        super().__init__(*args, **kwargs)
        self.participant_to_estimate: Dict[str, EstimatePayload] = {}

    def estimate(self, payload: EstimatePayload) -> None:
        """Handle an 'estimate' payload."""
        sender = payload.sender
        if sender not in self.period_state.participants:
            # sender not in the set of participants.
            return

        if sender in self.participant_to_estimate:
            # sender has already sent its estimate
            return

        self.participant_to_estimate[sender] = payload

    def check_estimate(self, payload: EstimatePayload) -> bool:
        """
        Check an estimate payload can be applied to the current state.

        An estimate transaction can be applied only if:
        - the round is in the 'estimate_consensus' state;
        - the sender belongs to the set of participants
        - the sender has not sent its estimate yet
        :param: payload: the payload.
        :return: True if the estimate tx is allowed, False otherwise.
        """
        sender_in_participant_set = payload.sender in self.period_state.participants
        sender_has_not_sent_estimate_yet = (
            payload.sender not in self.participant_to_estimate
        )
        return sender_in_participant_set and sender_has_not_sent_estimate_yet

    @property
    def estimate_threshold_reached(self) -> bool:
        """Check that the estimate threshold has been reached."""
        estimates_counter: CounterType = Counter()
        estimates_counter.update(
            payload.estimate for payload in self.participant_to_estimate.values()
        )
        # check that a single estimate has at least the consensu # of votes
        consensus_threshold = self._consensus_params.consensus_threshold
        return any(count >= consensus_threshold for count in estimates_counter.values())

    @property
    def most_voted_estimate(self) -> float:
        """Get the most voted estimate."""
        estimates_counter = Counter()  # type: ignore
        estimates_counter.update(
            payload.estimate for payload in self.participant_to_estimate.values()
        )
        most_voted_estimate, max_votes = max(
            estimates_counter.items(), key=itemgetter(1)
        )
        if max_votes < self._consensus_params.consensus_threshold:
            raise ValueError("estimate has not enough votes")
        return most_voted_estimate

    def end_block(self) -> Optional[Tuple[BasePeriodState, AbstractRound]]:
        """Process the end of the block."""
        if self.estimate_threshold_reached:
            state = self.period_state.update(
                participant_to_estimate=MappingProxyType(self.participant_to_estimate),
                most_voted_estimate=self.most_voted_estimate,
            )
            next_round = TxHashRound(state, self._consensus_params)
            return state, next_round
        return None


class TxHashRound(PriceEstimationAbstractRound):
    """
    This class represents the 'tx-hash' round.

    Input: a period state with the prior round data
    Ouptut: a new period state with the prior round data and the votes for each tx hash

    It schedules the CollectSignatureRound.
    """

    round_id = "tx_hash"

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the 'collect-signature' round."""
        super().__init__(*args, **kwargs)
        self.participant_to_tx_hash: Dict[str, TransactionHashPayload] = {}

    def tx_hash(self, payload: TransactionHashPayload) -> None:
        """Handle a 'tx_hash' payload."""
        sender = payload.sender
        if sender not in self.period_state.participants:
            # sender not in the set of participants.
            return

        if sender in self.participant_to_tx_hash:
            # sender has already sent its tx hash
            return

        self.participant_to_tx_hash[sender] = payload

    def check_tx_hash(self, payload: TransactionHashPayload) -> bool:
        """
        Check a signature payload can be applied to the current state.

        This can happen only if:
        - the round is in the 'tx_hash' state;
        - the sender belongs to the set of participants
        - the sender has not sent the tx_hash yet

        :param payload: the payload to check
        :return: True if the tx is allowed, False otherwise.
        """
        sender_in_participant_set = payload.sender in self.period_state.participants
        sender_has_not_sent_tx_hash_yet = (
            payload.sender not in self.participant_to_tx_hash
        )
        return sender_in_participant_set and sender_has_not_sent_tx_hash_yet

    @property
    def tx_threshold_reached(self) -> bool:
        """Check that the tx threshold has been reached."""
        tx_counter: CounterType = Counter()
        tx_counter.update(
            payload.tx_hash for payload in self.participant_to_tx_hash.values()
        )
        # check that a single estimate has at least the consensus # of votes
        consensus_threshold = self._consensus_params.consensus_threshold
        return any(count >= consensus_threshold for count in tx_counter.values())

    @property
    def most_voted_tx_hash(self) -> str:
        """Get the most voted tx hash."""
        tx_counter = Counter()  # type: ignore
        tx_counter.update(
            payload.tx_hash for payload in self.participant_to_tx_hash.values()
        )
        most_voted_tx_hash, max_votes = max(tx_counter.items(), key=itemgetter(1))
        if max_votes < self._consensus_params.consensus_threshold:
            raise ValueError("tx hash has not enough votes")
        return most_voted_tx_hash

    def end_block(self) -> Optional[Tuple[BasePeriodState, AbstractRound]]:
        """Process the end of the block."""
        if self.tx_threshold_reached:
            state = self.period_state.update(
                participant_to_tx_hash=MappingProxyType(self.participant_to_tx_hash),
                most_voted_tx_hash=self.most_voted_tx_hash,
            )
            next_round = CollectSignatureRound(state, self._consensus_params)
            return state, next_round
        return None


class CollectSignatureRound(PriceEstimationAbstractRound):
    """
    This class represents the 'collect-signature' round.

    Input: a period state with the prior round data
    Ouptut: a new period state with the prior round data and the signatures

    It schedules the FinalizationRound.
    """

    round_id = "collect_signature"

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the 'collect-signature' round."""
        super().__init__(*args, **kwargs)
        self.signatures_by_participant: Dict[str, str] = {}

    def signature(self, payload: SignaturePayload) -> None:
        """Handle a 'signature' payload."""
        sender = payload.sender
        if sender not in self.period_state.participants:
            # sender not in the set of participants.
            return

        if sender in self.signatures_by_participant:
            # sender has already sent its signature
            return

        self.signatures_by_participant[sender] = payload.signature

    def check_signature(self, payload: EstimatePayload) -> bool:
        """
        Check a signature payload can be applied to the current state.

        A signature transaction can be applied only if:
        - the round is in the 'collect-signature' state;
        - the sender belongs to the set of participants
        - the sender has not sent its signature yet

        :param: payload: the payload.
        :return: True if the signature tx is allowed, False otherwise.
        """
        sender_in_participant_set = payload.sender in self.period_state.participants
        sender_has_not_sent_signature_yet = (
            payload.sender not in self.signatures_by_participant
        )
        return sender_in_participant_set and sender_has_not_sent_signature_yet

    @property
    def signature_threshold_reached(self) -> bool:
        """Check that the signature threshold has been reached."""
        consensus_threshold = self._consensus_params.consensus_threshold
        return len(self.signatures_by_participant) >= consensus_threshold

    def end_block(self) -> Optional[Tuple[BasePeriodState, AbstractRound]]:
        """Process the end of the block."""
        if self.signature_threshold_reached:
            state = self.period_state.update(
                participant_to_signature=MappingProxyType(
                    self.signatures_by_participant
                ),
            )
            next_round = FinalizationRound(state, self._consensus_params)
            return state, next_round
        return None


class FinalizationRound(PriceEstimationAbstractRound):
    """
    This class represents the finalization Safe round.

    Input: a period state with the prior round data
    Output: a new period state with the prior round data and the hash of the Safe transaction

    It schedules the ValidateTransactionRound.
    """

    round_id = "finalization"

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the 'finalization' round."""
        super().__init__(*args, **kwargs)
        self._tx_hash: Optional[str] = None

    def finalization(self, payload: FinalizationTxPayload) -> None:
        """Handle a finalization payload."""
        sender = payload.sender

        if sender not in self.period_state.participants:
            # sender not in the set of participants.
            return

        if sender != self.period_state.most_voted_keeper_address:
            # the sender is not the elected sender
            return

        if self._tx_hash is not None:
            # transaction already set
            return

        self._tx_hash = payload.tx_hash

    def check_finalization(self, payload: DeploySafePayload) -> bool:
        """
        Check a finalization payload can be applied to the current state.

        A finalization transaction can be applied only if:
        - the sender belongs to the set of participants
        - the sender is the elected sender
        - the sender has not already sent the transaction hash

        :param: payload: the payload.
        :return: True if the finalization tx is allowed, False otherwise.
        """
        sender_in_participant_set = payload.sender in self.period_state.participants
        sender_is_elected_sender = (
            payload.sender == self.period_state.most_voted_keeper_address
        )
        tx_hash_not_set_yet = self._tx_hash is None
        return (
            sender_in_participant_set
            and sender_is_elected_sender
            and tx_hash_not_set_yet
        )

    @property
    def tx_hash_set(self) -> bool:
        """Check that the tx hash has been set."""
        return self._tx_hash is not None

    def end_block(self) -> Optional[Tuple[BasePeriodState, AbstractRound]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.tx_hash_set:
            state = self.period_state.update(final_tx_hash=self._tx_hash)
            next_round = ValidateTransactionRound(state, self._consensus_params)
            return state, next_round
        return None


class SelectKeeperARound(SelectKeeperRound):
    """This class represents the select keeper A round."""

    round_id = "select_keeper_a"
    next_round_class = DeploySafeRound

    def select_keeper_a(self, payload: SelectKeeperPayload) -> None:
        """Handle a 'select_keeper' payload."""
        super().select_keeper(payload)

    def check_select_keeper_a(self, payload: SelectKeeperPayload) -> bool:
        """Check an select_keeper payload can be applied to the current state."""
        return super().check_select_keeper(payload)


class SelectKeeperBRound(SelectKeeperRound):
    """This class represents the select keeper B round."""

    round_id = "select_keeper_b"
    next_round_class = FinalizationRound

    def select_keeper_b(self, payload: SelectKeeperPayload) -> None:
        """Handle a 'select_keeper' payload."""
        super().select_keeper(payload)

    def check_select_keeper_b(self, payload: SelectKeeperPayload) -> bool:
        """Check an select_keeper payload can be applied to the current state."""
        return super().check_select_keeper(payload)


class ConsensusReachedRound(PriceEstimationAbstractRound):
    """This class represents the 'consensus-reached' round (the final round)."""

    round_id = "consensus_reached"

    def end_block(self) -> Optional[Tuple[BasePeriodState, AbstractRound]]:
        """Process the end of the block."""
        return None


class ValidateSafeRound(ValidateRound):
    """
    This class represents the validate Safe round.

    Input: a period state with the prior round data
    Output: a new period state with the prior round data and the validation of the contract address

    It schedules the CollectObservationRound or SelectKeeperARound.
    """

    round_id = "validate_safe"
    positive_next_round_class = CollectObservationRound
    negative_next_round_class = SelectKeeperARound

    def validate_safe(self, payload: ValidatePayload) -> None:
        """
        Handle a validate payload.

        :param: payload: the payload.
        """
        super().validate(payload)

    def check_validate_safe(self, payload: ValidatePayload) -> bool:
        """
        Check a validate safe payload can be applied to the current state.

        A deploy safe transaction can be applied only if:
        - the sender belongs to the set of participants

        :param: payload: the payload.
        :return: True if the observation tx is allowed, False otherwise.
        """
        return super().check_validate(payload)


class ValidateTransactionRound(ValidateRound):
    """
    This class represents the validate transaction round.

    Input: a period state with the prior round data
    Output: a new period state with the prior round data and the validation of the transaction

    It schedules the ConsensusReachedRound or SelectKeeperARound.
    """

    round_id = "validate_transaction"
    positive_next_round_class = ConsensusReachedRound
    negative_next_round_class = SelectKeeperBRound

    def validate_transaction(self, payload: ValidatePayload) -> None:
        """
        Handle a validate payload.

        :param: payload: the payload.
        """
        super().validate(payload)

    def check_validate_transaction(self, payload: ValidatePayload) -> bool:
        """
        Check a validate transaction payload can be applied to the current state.

        A deploy safe transaction can be applied only if:
        - the sender belongs to the set of participants

        :param: payload: the payload.
        :return: True if the observation tx is allowed, False otherwise.
        """
        return super().check_validate(payload)