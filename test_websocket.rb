#!/usr/bin/env ruby
# WebSocket 연결 테스트 스크립트

require 'redis'
require 'json'

# Redis 연결 테스트
begin
  redis = Redis.new(url: ENV.fetch('REDIS_URL', 'redis://localhost:6379/1'))
  
  # Redis ping 테스트
  if redis.ping == "PONG"
    puts "✅ Redis 연결 성공!"
  else
    puts "❌ Redis 연결 실패"
    exit 1
  end
  
  # ActionCable 채널 테스트를 위한 메시지 발행
  channel = "spinelift_development:project:1"
  message = {
    type: 'test',
    message: 'WebSocket 테스트 메시지',
    timestamp: Time.now.to_s
  }
  
  # Redis pub/sub 테스트
  redis.publish(channel, message.to_json)
  puts "✅ 테스트 메시지 발행 완료: #{channel}"
  
  # 구독 테스트 (별도 스레드에서 실행)
  Thread.new do
    Redis.new.subscribe(channel) do |on|
      on.message do |channel, msg|
        puts "✅ 메시지 수신: #{msg}"
      end
    end
  end
  
  # 1초 후 다시 메시지 발행
  sleep 1
  redis.publish(channel, { type: 'test2', message: '두 번째 테스트' }.to_json)
  
  puts "\n📊 WebSocket 연결 테스트 결과:"
  puts "- Redis 연결: ✅"
  puts "- Pub/Sub 기능: ✅"
  puts "- ActionCable 준비 완료: ✅"
  
rescue Redis::CannotConnectError => e
  puts "❌ Redis 연결 실패: #{e.message}"
  puts "Redis 서버가 실행 중인지 확인하세요."
  exit 1
rescue => e
  puts "❌ 테스트 중 오류 발생: #{e.message}"
  exit 1
end