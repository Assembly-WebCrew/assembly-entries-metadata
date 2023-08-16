#!/usr/bin/ruby

require 'httparty'
require 'json'

PARTY="https://demozoo.org/api/v1/parties/4270/"

rr = HTTParty.get(PARTY, format: :plain)
party = JSON.parse(rr)

puts "Parsing #{party['name']}"

party['competitions'].each do |compo|
  puts
  puts ":section #{compo['name']}"
  puts
  
  compo['results'].each do |entry|
    ee = {}
    prod = entry['production']
    
    ee[:author] = prod['author_nicks'].map {|n| n['name'] }.join(", ")
    ee[:platform] = prod['platforms'].map {|n| n['name'] }.join(", ")
    ee[:position] = entry['ranking']
    ee[:title] = prod['title']
    
    dd = HTTParty.get(prod['url'], format: :plain)
    det = JSON.parse(dd)

    ee[:youtube] = 'TODO'

    det['download_links'].each do |link|
      if link['link_class'] == 'SceneOrgFile'
        ee[:sceneorg] = link['url'].gsub(/^.*scene.org\/view/, '')
      end
    end
    det['external_links'].each do |link|
      if link['link_class'] == 'PouetProduction'
        ee[:pouet] = link['url'].gsub(/^.*which=/, '')
      end
      if link['link_class'] == 'YoutubeVideo'
        ee[:youtube] = link['url'].gsub(/^.*watch.v=/, '')
      end
    end

    ss = []
    ee.each do |k,v|
      ss << "#{k}:#{v}"
    end
    puts ss.join("|")
  end
end

