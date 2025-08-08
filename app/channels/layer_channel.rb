class LayerChannel < ApplicationCable::Channel
  def subscribed
    layer = Layer.find(params[:layer_id])
    stream_for layer
  end
  
  def unsubscribed
    # Any cleanup needed when channel is unsubscribed
  end
end