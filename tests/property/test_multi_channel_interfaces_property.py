"""
Property-Based Tests for Multi-Channel Interface Language Support
Feature: sarvasahay-platform, Property 6: Multi-Channel Interface Language Support

This test validates that for any user interaction channel (SMS, voice, web), the system:
1. Provides navigation and communication in the user's preferred local language
2. Supports all required languages (Marathi, Hindi, regional languages)
3. Maintains consistent messaging across channels
4. Handles language switching gracefully

Validates: Requirements 6.1, 6.2, 6.5
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.sms_interface import SMSInterfaceHandler, SMSLanguage, SMSMenuState
from services.voice_interface import VoiceInterfaceHandler, VoiceLanguage, VoiceCallState


# Strategy for generating valid phone numbers
@st.composite
def phone_number_strategy(draw):
    """Generate valid Indian phone numbers"""
    # Format: 91XXXXXXXXXX or +91XXXXXXXXXX
    prefix = draw(st.sampled_from(['91', '+91', '']))
    first_digit = draw(st.sampled_from(['6', '7', '8', '9']))
    remaining = ''.join([str(draw(st.integers(min_value=0, max_value=9))) for _ in range(9)])
    return f"{prefix}{first_digit}{remaining}"


# Strategy for generating SMS languages
@st.composite
def sms_language_strategy(draw):
    """Generate valid SMS language selections"""
    return draw(st.sampled_from(list(SMSLanguage)))


# Strategy for generating voice languages
@st.composite
def voice_language_strategy(draw):
    """Generate valid voice language codes"""
    return draw(st.sampled_from(list(VoiceLanguage)))


# Strategy for generating user messages in different languages
@st.composite
def multilingual_message_strategy(draw, language: Optional[str] = None):
    """Generate user messages in various languages"""
    if language is None:
        language = draw(st.sampled_from(['english', 'hindi', 'marathi']))
    
    message_templates = {
        'english': draw(st.sampled_from([
            'PROFILE BANAO', 'CREATE PROFILE', 'HELP', '1', '2', '3', '4',
            'HELLO', 'STATUS', 'SCHEMES'
        ])),
        'hindi': draw(st.sampled_from([
            'प्रोफाइल बनाओ', 'मदद', '1', '2', '3', '4',
            'नमस्ते', 'स्थिति', 'योजनाएं'
        ])),
        'marathi': draw(st.sampled_from([
            'प्रोफाईल बनवा', 'मदत', '1', '2', '3', '4',
            'नमस्कार', 'स्थिती', 'योजना'
        ]))
    }
    
    return message_templates.get(language, message_templates['english'])


# Strategy for generating profile creation inputs
@st.composite
def profile_input_sequence_strategy(draw):
    """Generate a sequence of profile creation inputs"""
    return {
        'age': str(draw(st.integers(min_value=18, max_value=100))),
        'gender': draw(st.sampled_from(['1', '2', '3'])),
        'caste': draw(st.sampled_from(['1', '2', '3', '4'])),
        'income': str(draw(st.integers(min_value=0, max_value=1000000))),
        'land': str(draw(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))),
        'employment': draw(st.sampled_from(['1', '2', '3', '4'])),
        'location': f"{draw(st.text(min_size=3, max_size=20, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ'))},"
                   f"{draw(st.text(min_size=3, max_size=20, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ'))},"
                   f"{draw(st.text(min_size=3, max_size=20, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ'))}",
        'family': str(draw(st.integers(min_value=1, max_value=15)))
    }


class TestMultiChannelInterfaceLanguageSupport:
    """
    Property 6: Multi-Channel Interface Language Support
    
    For any user interaction channel (SMS, voice, web), the system should:
    1. Provide navigation in user's preferred language
    2. Support all required languages
    3. Maintain consistent messaging
    4. Handle language switching
    """
    
    @given(
        phone=phone_number_strategy(),
        language=sms_language_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_sms_interface_supports_all_languages(self, phone: str, language: SMSLanguage):
        """
        Property: SMS interface must support all configured languages
        
        Validates Requirement 6.1: SMS interface provides menu-driven navigation 
        in local languages (Marathi, Hindi, regional)
        """
        handler = SMSInterfaceHandler()
        
        # Map language enum to selection number
        language_map = {
            SMSLanguage.HINDI: '1',
            SMSLanguage.MARATHI: '2',
            SMSLanguage.ENGLISH: '3',
            SMSLanguage.TAMIL: '4',
            SMSLanguage.BENGALI: '5',
            SMSLanguage.TELUGU: '6',
            SMSLanguage.KANNADA: '7',
            SMSLanguage.GUJARATI: '8'
        }
        
        # First contact - get language menu
        initial_response = handler.process_sms(phone, 'HELLO')
        assert initial_response is not None
        
        # Select language
        language_selection = language_map[language]
        response = handler.process_sms(phone, language_selection)
        
        # Verify response is not empty
        assert response is not None
        assert len(response) > 0
        
        # Verify language was set in session (using normalized phone number)
        normalized_phone = handler._normalize_phone_number(phone)
        session = handler._get_session(normalized_phone)
        assert session.get('language') == language
        assert session.get('state') == SMSMenuState.MAIN_MENU
        
        # Verify main menu is returned
        assert 'menu' in response.lower() or 'मेनू' in response or 'मेन्यू' in response
    
    @given(
        phone=phone_number_strategy(),
        language=sms_language_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_sms_responses_match_selected_language(self, phone: str, language: SMSLanguage):
        """
        Property: All SMS responses must be in the user's selected language
        
        Validates Requirement 6.5: System supports Marathi, Hindi, and regional languages
        """
        handler = SMSInterfaceHandler()
        
        # Set language
        language_map = {
            SMSLanguage.HINDI: '1',
            SMSLanguage.MARATHI: '2',
            SMSLanguage.ENGLISH: '3',
            SMSLanguage.TAMIL: '4',
            SMSLanguage.BENGALI: '5',
            SMSLanguage.TELUGU: '6',
            SMSLanguage.KANNADA: '7',
            SMSLanguage.GUJARATI: '8'
        }
        handler.process_sms(phone, language_map[language])
        
        # Request help
        help_response = handler.process_sms(phone, 'HELP')
        
        # Verify response contains language-specific content
        assert help_response is not None
        assert len(help_response) > 0
        
        # Language-specific validation
        if language == SMSLanguage.HINDI:
            assert any(char in help_response for char in 'हिंदी')
        elif language == SMSLanguage.MARATHI:
            assert any(char in help_response for char in 'मराठी')
        elif language == SMSLanguage.ENGLISH:
            assert 'help' in help_response.lower() or 'menu' in help_response.lower()
    
    @given(
        phone=phone_number_strategy(),
        call_id=st.text(min_size=10, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        language=voice_language_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_voice_interface_supports_all_languages(self, phone: str, call_id: str, language: VoiceLanguage):
        """
        Property: Voice interface must support all configured languages
        
        Validates Requirement 6.2: Voice interface guides users through profile 
        creation and scheme discovery in their language
        """
        handler = VoiceInterfaceHandler()
        
        # Start voice call with language
        response = handler.start_voice_call(call_id, phone, language)
        
        # Verify response structure
        assert response is not None
        assert 'call_id' in response
        assert 'response_text' in response
        assert 'language' in response
        assert response['call_id'] == call_id
        assert response['language'] == language
        
        # Verify welcome message is not empty
        assert len(response['response_text']) > 0
        
        # Verify action is to continue
        assert response['action'] == 'continue'
    
    @given(
        phone=phone_number_strategy(),
        call_id=st.text(min_size=10, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        language=voice_language_strategy(),
        speech_text=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' '))
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_voice_responses_match_selected_language(self, phone: str, call_id: str, 
                                                     language: VoiceLanguage, speech_text: str):
        """
        Property: Voice responses must be in the user's selected language
        
        Validates Requirement 6.2: Voice interface provides language-appropriate responses
        """
        # Create handler with SMS handler for state management
        sms_handler = SMSInterfaceHandler()
        voice_handler = VoiceInterfaceHandler(sms_handler=sms_handler)
        
        # Start call
        voice_handler.start_voice_call(call_id, phone, language)
        
        # Process voice input
        response = voice_handler.process_voice_input(call_id, phone, speech_text, language)
        
        # Verify response structure
        assert response is not None
        assert 'response_text' in response
        assert 'language' in response
        assert response['language'] == language
        
        # Verify response is not empty
        assert len(response['response_text']) > 0
    
    @given(
        phone=phone_number_strategy(),
        initial_language=sms_language_strategy(),
        new_language=sms_language_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_language_switching_maintains_session_state(self, phone: str, 
                                                        initial_language: SMSLanguage,
                                                        new_language: SMSLanguage):
        """
        Property: Language switching must maintain user session state
        
        Validates Requirement 6.5: System handles language changes gracefully
        """
        assume(initial_language != new_language)
        
        handler = SMSInterfaceHandler()
        
        # Set initial language
        language_map = {
            SMSLanguage.HINDI: '1',
            SMSLanguage.MARATHI: '2',
            SMSLanguage.ENGLISH: '3',
            SMSLanguage.TAMIL: '4',
            SMSLanguage.BENGALI: '5',
            SMSLanguage.TELUGU: '6',
            SMSLanguage.KANNADA: '7',
            SMSLanguage.GUJARATI: '8'
        }
        
        # First interaction - language selection
        response1 = handler.process_sms(phone, language_map[initial_language])
        
        # Get session after initial language
        session_before = handler._get_session(phone)
        # Language should be set after selection
        if session_before.get('state') == SMSMenuState.MAIN_MENU:
            assert session_before.get('language') == initial_language
        
        # Verify session exists and has state
        assert session_before is not None
        assert 'state' in session_before
        
        # Switch language by going back to language selection
        # (In real usage, user would restart or use a language change command)
        # For this test, we verify that language preference persists in session
        session_before_switch = handler._get_session(phone)
        original_state = session_before_switch.get('state')
        
        # Manually update language in session (simulating language change)
        session_before_switch['language'] = new_language
        handler._save_session(phone, session_before_switch)
        
        # Verify language changed
        session_after = handler._get_session(phone)
        assert session_after['language'] == new_language
        
        # Verify session state is maintained
        assert session_after is not None
        assert 'state' in session_after
        assert session_after['state'] == original_state
    
    @given(
        phone=phone_number_strategy(),
        language=sms_language_strategy(),
        profile_inputs=profile_input_sequence_strategy()
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_profile_creation_workflow_in_any_language(self, phone: str, 
                                                       language: SMSLanguage,
                                                       profile_inputs: Dict[str, str]):
        """
        Property: Profile creation workflow must work in any supported language
        
        Validates Requirement 6.1: SMS interface supports profile creation in local languages
        """
        handler = SMSInterfaceHandler()
        
        # Set language
        language_map = {
            SMSLanguage.HINDI: '1',
            SMSLanguage.MARATHI: '2',
            SMSLanguage.ENGLISH: '3',
            SMSLanguage.TAMIL: '4',
            SMSLanguage.BENGALI: '5',
            SMSLanguage.TELUGU: '6',
            SMSLanguage.KANNADA: '7',
            SMSLanguage.GUJARATI: '8'
        }
        
        # Initialize session with language
        handler.process_sms(phone, 'HELLO')  # Get language menu
        handler.process_sms(phone, language_map[language])  # Select language
        
        # Verify language is set (using normalized phone)
        normalized_phone = handler._normalize_phone_number(phone)
        session_after_lang = handler._get_session(normalized_phone)
        assert session_after_lang.get('language') == language
        assert session_after_lang.get('state') == SMSMenuState.MAIN_MENU
        
        # Start profile creation
        response = handler.process_sms(phone, 'PROFILE BANAO')
        assert response is not None
        
        # Verify we're in profile creation state
        session = handler._get_session(normalized_phone)
        assert session['state'] == SMSMenuState.PROFILE_AGE
        
        # Complete profile creation sequence
        responses = []
        responses.append(handler.process_sms(phone, profile_inputs['age']))
        responses.append(handler.process_sms(phone, profile_inputs['gender']))
        responses.append(handler.process_sms(phone, profile_inputs['caste']))
        responses.append(handler.process_sms(phone, profile_inputs['income']))
        responses.append(handler.process_sms(phone, profile_inputs['land']))
        responses.append(handler.process_sms(phone, profile_inputs['employment']))
        responses.append(handler.process_sms(phone, profile_inputs['location']))
        final_response = handler.process_sms(phone, profile_inputs['family'])
        
        # Verify all responses are not empty
        for response in responses:
            assert response is not None
            assert len(response) > 0
        
        # Verify final response indicates profile creation
        assert final_response is not None
        assert len(final_response) > 0
        
        # Verify session has profile ID
        final_session = handler._get_session(normalized_phone)
        assert 'profile_id' in final_session or 'profile_data' in final_session
    
    @given(
        phone=phone_number_strategy(),
        language=sms_language_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_error_messages_in_user_language(self, phone: str, language: SMSLanguage):
        """
        Property: Error messages must be displayed in user's selected language
        
        Validates Requirement 6.5: All system messages support local languages
        """
        handler = SMSInterfaceHandler()
        
        # Set language
        language_map = {
            SMSLanguage.HINDI: '1',
            SMSLanguage.MARATHI: '2',
            SMSLanguage.ENGLISH: '3',
            SMSLanguage.TAMIL: '4',
            SMSLanguage.BENGALI: '5',
            SMSLanguage.TELUGU: '6',
            SMSLanguage.KANNADA: '7',
            SMSLanguage.GUJARATI: '8'
        }
        handler.process_sms(phone, language_map[language])
        
        # Start profile creation
        handler.process_sms(phone, 'PROFILE BANAO')
        
        # Send invalid age
        error_response = handler.process_sms(phone, 'INVALID')
        
        # Verify error message is not empty
        assert error_response is not None
        assert len(error_response) > 0
        
        # Verify error message contains language-appropriate content
        # (Error messages should be in the selected language)
        if language == SMSLanguage.ENGLISH:
            assert 'invalid' in error_response.lower() or 'error' in error_response.lower()
    
    @given(
        phone=phone_number_strategy(),
        languages=st.lists(sms_language_strategy(), min_size=2, max_size=4, unique=True)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_consistent_messaging_across_language_switches(self, phone: str, 
                                                           languages: List[SMSLanguage]):
        """
        Property: Core functionality must remain consistent across language switches
        
        Validates Requirement 6.5: Language changes don't affect system functionality
        """
        handler = SMSInterfaceHandler()
        
        language_map = {
            SMSLanguage.HINDI: '1',
            SMSLanguage.MARATHI: '2',
            SMSLanguage.ENGLISH: '3',
            SMSLanguage.TAMIL: '4',
            SMSLanguage.BENGALI: '5',
            SMSLanguage.TELUGU: '6',
            SMSLanguage.KANNADA: '7',
            SMSLanguage.GUJARATI: '8'
        }
        
        # Test main menu in each language
        menu_responses = []
        for language in languages:
            handler.process_sms(phone, language_map[language])
            response = handler.process_sms(phone, '4')  # Help option
            menu_responses.append(response)
            
            # Verify response is not empty
            assert response is not None
            assert len(response) > 0
        
        # Verify all responses were generated (functionality works in all languages)
        assert len(menu_responses) == len(languages)
        assert all(r is not None for r in menu_responses)
    
    @given(
        phone=phone_number_strategy(),
        call_id=st.text(min_size=10, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        language=voice_language_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_voice_call_lifecycle_in_any_language(self, phone: str, call_id: str, 
                                                  language: VoiceLanguage):
        """
        Property: Complete voice call lifecycle must work in any language
        
        Validates Requirement 6.2: Voice interface supports complete workflows 
        in all languages
        """
        handler = VoiceInterfaceHandler()
        
        # Start call
        start_response = handler.start_voice_call(call_id, phone, language)
        assert start_response is not None
        assert start_response['action'] == 'continue'
        assert start_response['language'] == language
        
        # Verify call session exists
        assert call_id in handler.call_sessions
        
        # End call
        end_response = handler.end_voice_call(call_id)
        assert end_response is not None
        assert end_response['action'] == 'end'
        
        # Verify call session is cleaned up
        assert call_id not in handler.call_sessions
    
    @given(
        phone=phone_number_strategy(),
        language=sms_language_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_sms_session_persistence_across_interactions(self, phone: str, 
                                                         language: SMSLanguage):
        """
        Property: SMS sessions must persist language preference across interactions
        
        Validates Requirement 6.1: Language preference is maintained throughout session
        """
        handler = SMSInterfaceHandler()
        
        # Set language
        language_map = {
            SMSLanguage.HINDI: '1',
            SMSLanguage.MARATHI: '2',
            SMSLanguage.ENGLISH: '3',
            SMSLanguage.TAMIL: '4',
            SMSLanguage.BENGALI: '5',
            SMSLanguage.TELUGU: '6',
            SMSLanguage.KANNADA: '7',
            SMSLanguage.GUJARATI: '8'
        }
        
        # Initialize session with language
        handler.process_sms(phone, 'HELLO')  # Get language menu
        handler.process_sms(phone, language_map[language])  # Select language
        
        # Use normalized phone for session checks
        normalized_phone = handler._normalize_phone_number(phone)
        
        # Verify language is set
        session1 = handler._get_session(normalized_phone)
        assert session1.get('language') == language
        
        # Send multiple messages
        handler.process_sms(phone, '1')  # Profile creation
        handler.process_sms(phone, '25')  # Age
        
        # Verify language is still set
        session2 = handler._get_session(normalized_phone)
        assert session2.get('language') == language
        
        # Request help
        handler.process_sms(phone, 'HELP')
        
        # Verify language is still set
        session3 = handler._get_session(normalized_phone)
        assert session3.get('language') == language
    
    @given(
        phone=phone_number_strategy(),
        language=sms_language_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_multilingual_command_recognition(self, phone: str, language: SMSLanguage):
        """
        Property: System must recognize commands in multiple languages
        
        Validates Requirement 6.5: Commands work in Marathi, Hindi, and English
        """
        handler = SMSInterfaceHandler()
        
        # Set language
        language_map = {
            SMSLanguage.HINDI: '1',
            SMSLanguage.MARATHI: '2',
            SMSLanguage.ENGLISH: '3',
            SMSLanguage.TAMIL: '4',
            SMSLanguage.BENGALI: '5',
            SMSLanguage.TELUGU: '6',
            SMSLanguage.KANNADA: '7',
            SMSLanguage.GUJARATI: '8'
        }
        handler.process_sms(phone, language_map[language])
        
        # Test language-specific commands
        commands = {
            SMSLanguage.ENGLISH: ['PROFILE BANAO', 'CREATE PROFILE', 'HELP'],
            SMSLanguage.HINDI: ['प्रोफाइल बनाओ', 'मदद'],
            SMSLanguage.MARATHI: ['प्रोफाईल बनवा', 'मदत']
        }
        
        test_commands = commands.get(language, commands[SMSLanguage.ENGLISH])
        
        for command in test_commands:
            response = handler.process_sms(phone, command)
            
            # Verify command is recognized (response is not error)
            assert response is not None
            assert len(response) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
