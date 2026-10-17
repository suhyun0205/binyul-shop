// 모든 페이지가 공유하는 Supabase 클라이언트 (publishable 키는 공개용이라 그대로 사용 가능)
var supabaseClient = supabase.createClient(
  'https://zcxzelfnshxzbenorblj.supabase.co',
  'sb_publishable_Dai0tnACM-C1F-vjMlMYKg_KmsZKeNi'
);

// Supabase 인증 에러 메시지를 한국어로 변환
function translateAuthError(message) {
  var map = {
    'Invalid login credentials': '이메일 또는 비밀번호가 올바르지 않습니다.',
    'User already registered': '이미 가입된 이메일입니다.',
    'Password should be at least 6 characters': '비밀번호는 6자 이상이어야 합니다.',
    'Unable to validate email address: invalid format': '이메일 형식이 올바르지 않습니다.',
    'Email not confirmed': '이메일 인증이 필요합니다. 메일함을 확인해주세요.'
  };
  return map[message] || ('오류가 발생했습니다: ' + message);
}
